"""
NC1709 DeepFabric Training Script
Optimized for A100 80GB GPU with Unsloth for efficient fine-tuning
"""

import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any
import torch
from datasets import Dataset, load_from_disk
from transformers import (
    AutoTokenizer,
    TrainingArguments,
    EarlyStoppingCallback,
    Trainer
)
from unsloth import FastLanguageModel, is_bfloat16_supported
from trl import SFTTrainer
import wandb
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NC1709Trainer:
    """
    High-performance trainer for NC1709 DeepFabric models
    Optimized for A100 GPU with memory efficiency and speed
    """
    
    def __init__(self, args):
        self.args = args
        self.model = None
        self.tokenizer = None
        self.trainer = None
        
        # A100 optimizations
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        # Initialize wandb if enabled
        if args.use_wandb:
            wandb.init(
                project="nc1709-deepfabric",
                name=f"training-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                config=vars(args)
            )
    
    def setup_model(self):
        """Setup model and tokenizer with Unsloth optimizations"""
        logger.info(f"Loading model: {self.args.model_name}")
        
        # Load model with Unsloth for 2x faster training
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.args.model_name,
            max_seq_length=self.args.max_seq_length,
            dtype=torch.float16 if not is_bfloat16_supported() else torch.bfloat16,
            load_in_4bit=self.args.load_in_4bit,  # Use 4bit to save memory
            device_map="auto"
        )
        
        # Setup LoRA for efficient fine-tuning
        if self.args.use_lora:
            self.model = FastLanguageModel.get_peft_model(
                self.model,
                r=self.args.lora_rank,
                target_modules=self.args.target_modules.split(","),
                lora_alpha=self.args.lora_alpha,
                lora_dropout=self.args.lora_dropout,
                bias="none",
                use_gradient_checkpointing=True,  # Save memory
                random_state=42
            )
        
        # Print model info
        logger.info(f"Model loaded: {self.model.get_model_status()}")
        
        # Setup tokenizer
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
    
    def load_dataset(self):
        """Load and prepare training dataset"""
        logger.info(f"Loading dataset from: {self.args.dataset_path}")
        
        # Load dataset splits
        train_data = self._load_jsonl(f"{self.args.dataset_path}/train.jsonl")
        val_data = self._load_jsonl(f"{self.args.dataset_path}/validation.jsonl")
        
        logger.info(f"Train examples: {len(train_data):,}")
        logger.info(f"Validation examples: {len(val_data):,}")
        
        # Convert to datasets format
        train_dataset = Dataset.from_list(train_data)
        val_dataset = Dataset.from_list(val_data)
        
        # Tokenize datasets
        train_dataset = train_dataset.map(
            self._tokenize_function,
            batched=True,
            remove_columns=train_dataset.column_names,
            desc="Tokenizing training data"
        )
        
        val_dataset = val_dataset.map(
            self._tokenize_function,
            batched=True,
            remove_columns=val_dataset.column_names,
            desc="Tokenizing validation data"
        )
        
        return train_dataset, val_dataset
    
    def _load_jsonl(self, file_path: str) -> list:
        """Load JSONL file"""
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                data.append(json.loads(line))
        return data
    
    def _tokenize_function(self, examples):
        """Tokenize examples for training"""
        # Convert training examples to text format
        texts = []
        for i in range(len(examples['user_input'])):
            # Format: [INPUT] user_input [TOOLS] tool_calls [OUTPUT] expected_output
            tool_calls_str = self._format_tool_calls(examples['tool_calls'][i])
            
            text = f"[INPUT] {examples['user_input'][i]} [TOOLS] {tool_calls_str} [OUTPUT] {examples['expected_output'][i]}"
            texts.append(text)
        
        # Tokenize
        tokenized = self.tokenizer(
            texts,
            truncation=True,
            padding=False,
            max_length=self.args.max_seq_length,
            return_tensors=None
        )
        
        # Set labels (same as input_ids for causal LM)
        tokenized["labels"] = tokenized["input_ids"].copy()
        
        return tokenized
    
    def _format_tool_calls(self, tool_calls: list) -> str:
        """Format tool calls for training text"""
        formatted_calls = []
        for call in tool_calls:
            formatted = f"{call['tool_name']}({json.dumps(call['parameters'])})"
            formatted_calls.append(formatted)
        
        return " -> ".join(formatted_calls)
    
    def setup_training(self, train_dataset, val_dataset):
        """Setup training configuration"""
        # Calculate steps
        num_train_examples = len(train_dataset)
        steps_per_epoch = num_train_examples // self.args.batch_size
        total_steps = steps_per_epoch * self.args.num_epochs
        
        logger.info(f"Training steps per epoch: {steps_per_epoch}")
        logger.info(f"Total training steps: {total_steps}")
        
        # Training arguments optimized for A100
        training_args = TrainingArguments(
            output_dir=self.args.output_dir,
            num_train_epochs=self.args.num_epochs,
            per_device_train_batch_size=self.args.batch_size,
            per_device_eval_batch_size=self.args.batch_size,
            gradient_accumulation_steps=self.args.gradient_accumulation_steps,
            
            # Optimizer settings
            learning_rate=self.args.learning_rate,
            weight_decay=self.args.weight_decay,
            warmup_steps=self.args.warmup_steps,
            max_grad_norm=self.args.max_grad_norm,
            
            # Mixed precision for A100
            fp16=not is_bfloat16_supported() and self.args.fp16,
            bf16=is_bfloat16_supported() and self.args.fp16,
            dataloader_pin_memory=False,  # Faster on A100
            
            # Logging and saving
            logging_dir=f"{self.args.output_dir}/logs",
            logging_steps=self.args.logging_steps,
            save_steps=self.args.save_steps,
            save_total_limit=3,
            
            # Evaluation
            evaluation_strategy=self.args.evaluation_strategy,
            eval_steps=self.args.eval_steps,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            
            # Memory optimization
            gradient_checkpointing=self.args.gradient_checkpointing,
            dataloader_num_workers=4,
            remove_unused_columns=False,
            
            # Reporting
            report_to="wandb" if self.args.use_wandb else None,
            run_name=f"nc1709-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            
            # A100 specific optimizations
            ddp_find_unused_parameters=False,
            torch_compile=True,  # PyTorch 2.0 compilation
        )
        
        # Setup trainer with Unsloth SFT
        self.trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            dataset_text_field="text",  # Will be handled by tokenize function
            max_seq_length=self.args.max_seq_length,
            args=training_args,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
        )
    
    def train(self):
        """Execute training"""
        logger.info("Starting training...")
        start_time = time.time()
        
        # Train the model
        try:
            train_result = self.trainer.train()
            
            # Log training results
            training_time = time.time() - start_time
            logger.info(f"Training completed in {training_time/3600:.2f} hours")
            logger.info(f"Final train loss: {train_result.training_loss:.4f}")
            
            # Save final model
            self.save_model()
            
            # Log final metrics
            if self.args.use_wandb:
                wandb.log({
                    "final_train_loss": train_result.training_loss,
                    "training_time_hours": training_time / 3600,
                    "total_steps": train_result.global_step
                })
            
            return train_result
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
    
    def save_model(self):
        """Save trained model"""
        logger.info(f"Saving model to {self.args.output_dir}")
        
        # Save with Unsloth (faster saving)
        if self.args.use_lora:
            self.model.save_pretrained(f"{self.args.output_dir}/lora_model")
            self.tokenizer.save_pretrained(f"{self.args.output_dir}/lora_model")
            
            # Also save merged model for inference
            merged_model = FastLanguageModel.for_inference(self.model)
            merged_model.save_pretrained(f"{self.args.output_dir}/merged_model")
        else:
            self.model.save_pretrained(f"{self.args.output_dir}/full_model")
            self.tokenizer.save_pretrained(f"{self.args.output_dir}/full_model")
        
        # Save training config
        config = {
            "model_name": self.args.model_name,
            "training_args": vars(self.args),
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": self._get_performance_metrics()
        }
        
        with open(f"{self.args.output_dir}/training_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info("Model saved successfully")
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get training performance metrics"""
        if hasattr(self.trainer, 'state') and self.trainer.state.log_history:
            logs = self.trainer.state.log_history
            
            # Extract key metrics
            train_losses = [log.get('train_loss') for log in logs if 'train_loss' in log]
            eval_losses = [log.get('eval_loss') for log in logs if 'eval_loss' in log]
            
            return {
                "best_train_loss": min(train_losses) if train_losses else None,
                "best_eval_loss": min(eval_losses) if eval_losses else None,
                "total_steps": self.trainer.state.global_step,
                "total_epochs": self.trainer.state.epoch,
            }
        
        return {}
    
    def evaluate(self, dataset):
        """Evaluate model on dataset"""
        logger.info("Running evaluation...")
        
        eval_result = self.trainer.evaluate(eval_dataset=dataset)
        
        logger.info(f"Evaluation results: {eval_result}")
        
        if self.args.use_wandb:
            wandb.log({"final_eval": eval_result})
        
        return eval_result


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Train NC1709 DeepFabric model")
    
    # Model arguments
    parser.add_argument("--model_name", type=str, default="Qwen/Qwen2.5-Coder-7B",
                       help="Base model to fine-tune")
    parser.add_argument("--max_seq_length", type=int, default=2048,
                       help="Maximum sequence length")
    
    # Dataset arguments
    parser.add_argument("--dataset_path", type=str, required=True,
                       help="Path to training dataset")
    
    # Training arguments
    parser.add_argument("--output_dir", type=str, default="./checkpoints",
                       help="Output directory for checkpoints")
    parser.add_argument("--num_epochs", type=int, default=3,
                       help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32,
                       help="Training batch size")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=1,
                       help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-4,
                       help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=0.01,
                       help="Weight decay")
    parser.add_argument("--warmup_steps", type=int, default=500,
                       help="Warmup steps")
    parser.add_argument("--max_grad_norm", type=float, default=1.0,
                       help="Max gradient norm for clipping")
    
    # LoRA arguments
    parser.add_argument("--use_lora", action="store_true",
                       help="Use LoRA for efficient fine-tuning")
    parser.add_argument("--lora_rank", type=int, default=256,
                       help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=256,
                       help="LoRA alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.1,
                       help="LoRA dropout")
    parser.add_argument("--target_modules", type=str, 
                       default="q_proj,v_proj,k_proj,o_proj",
                       help="Target modules for LoRA")
    
    # Optimization arguments
    parser.add_argument("--fp16", action="store_true",
                       help="Use mixed precision training")
    parser.add_argument("--gradient_checkpointing", action="store_true",
                       help="Use gradient checkpointing to save memory")
    parser.add_argument("--load_in_4bit", action="store_true",
                       help="Load model in 4bit for memory efficiency")
    
    # Logging and evaluation
    parser.add_argument("--logging_steps", type=int, default=10,
                       help="Logging frequency")
    parser.add_argument("--save_steps", type=int, default=500,
                       help="Save checkpoint frequency")
    parser.add_argument("--evaluation_strategy", type=str, default="steps",
                       choices=["no", "steps", "epoch"],
                       help="Evaluation strategy")
    parser.add_argument("--eval_steps", type=int, default=100,
                       help="Evaluation frequency")
    parser.add_argument("--use_wandb", action="store_true",
                       help="Use Weights & Biases for logging")
    
    return parser.parse_args()


def main():
    """Main training function"""
    args = parse_args()
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize trainer
    trainer = NC1709Trainer(args)
    
    # Setup model
    trainer.setup_model()
    
    # Load dataset
    train_dataset, val_dataset = trainer.load_dataset()
    
    # Setup training
    trainer.setup_training(train_dataset, val_dataset)
    
    # Start training
    train_result = trainer.train()
    
    # Final evaluation
    eval_result = trainer.evaluate(val_dataset)
    
    logger.info("Training pipeline completed successfully!")
    logger.info(f"Best model saved to: {args.output_dir}")
    
    # Print summary
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)
    print(f"Model: {args.model_name}")
    print(f"Training Loss: {train_result.training_loss:.4f}")
    print(f"Validation Loss: {eval_result['eval_loss']:.4f}")
    print(f"Total Steps: {train_result.global_step}")
    print(f"Output Directory: {args.output_dir}")
    print("="*80)


if __name__ == "__main__":
    main()