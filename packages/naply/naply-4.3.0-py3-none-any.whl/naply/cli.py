"""
NAPLY Command Line Interface
============================

Command-line tools for training and using NAPLY models.

Usage:
    naply train --data my_data/ --epochs 10
    naply chat my_model/
    naply info
"""

import argparse
import sys
from typing import Optional


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NAPLY - Build AI models from scratch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  naply train --data my_data/ --epochs 10 --output my_model
  naply chat my_model/
  naply generate my_model/ --prompt "Hello"
  naply info
  naply methods
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train a new model')
    train_parser.add_argument('--data', '-d', required=True, help='Path to training data')
    train_parser.add_argument('--output', '-o', default='naply_model', help='Output path for model')
    train_parser.add_argument('--epochs', '-e', type=int, default=5, help='Number of epochs')
    train_parser.add_argument('--batch-size', '-b', type=int, default=32, help='Batch size')
    train_parser.add_argument('--learning-rate', '-lr', type=float, default=1e-4, help='Learning rate')
    train_parser.add_argument('--layers', type=int, default=12, help='Number of layers')
    train_parser.add_argument('--heads', type=int, default=12, help='Number of attention heads')
    train_parser.add_argument('--embedding', type=int, default=768, help='Embedding dimension')
    train_parser.add_argument('--vocab-size', type=int, default=30000, help='Vocabulary size')
    train_parser.add_argument('--context', type=int, default=512, help='Context length')
    train_parser.add_argument('--preset', choices=['tiny', 'small', 'medium', 'large', 'xl'], 
                             help='Use a preset configuration')
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Chat with a trained model')
    chat_parser.add_argument('model', help='Path to trained model')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate text from a model')
    gen_parser.add_argument('model', help='Path to trained model')
    gen_parser.add_argument('--prompt', '-p', required=True, help='Prompt text')
    gen_parser.add_argument('--max-tokens', '-m', type=int, default=100, help='Max tokens to generate')
    gen_parser.add_argument('--temperature', '-t', type=float, default=0.8, help='Sampling temperature')
    
    # Info command
    subparsers.add_parser('info', help='Show NAPLY version and info')
    
    # Methods command
    subparsers.add_parser('methods', help='List available training methods')
    
    args = parser.parse_args()
    
    if args.command == 'train':
        cmd_train(args)
    elif args.command == 'chat':
        cmd_chat(args)
    elif args.command == 'generate':
        cmd_generate(args)
    elif args.command == 'info':
        cmd_info()
    elif args.command == 'methods':
        cmd_methods()
    else:
        parser.print_help()


def cmd_train(args):
    """Train a new model."""
    from .model import Model
    
    print("🚀 NAPLY - Training New Model")
    print("=" * 40)
    
    if args.preset:
        model = Model(args.preset)
    else:
        model = Model(
            layers=args.layers,
            heads=args.heads,
            embedding=args.embedding,
            vocab_size=args.vocab_size,
            context=args.context
        )
    
    print(model.summary())
    print()
    
    model.train(
        data_path=args.data,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        output_dir=args.output
    )
    
    model.save(args.output)
    print(f"\n✅ Model saved to: {args.output}")


def cmd_chat(args):
    """Chat with a trained model."""
    from .model import Model
    
    print("🤖 NAPLY Chat")
    print("=" * 40)
    print("Loading model...")
    
    model = Model.load(args.model)
    
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            if not user_input:
                continue
            
            response = model.chat(user_input)
            print(f"AI: {response}\n")
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break


def cmd_generate(args):
    """Generate text from a model."""
    from .model import Model
    
    model = Model.load(args.model)
    
    text = model.generate(
        args.prompt,
        max_tokens=args.max_tokens,
        temperature=args.temperature
    )
    
    print(text)


def cmd_info():
    """Show NAPLY info."""
    from . import __version__
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                         NAPLY                             ║
║          Build Powerful AI Models From Scratch            ║
╠═══════════════════════════════════════════════════════════╣
║  Version: {__version__:^47}  ║
║                                                           ║
║  Features:                                                ║
║  ✅ No limits on model size                               ║
║  ✅ Any dataset format (txt, json, jsonl, csv)            ║
║  ✅ 10 advanced training methods                          ║
║  ✅ From scratch - no PyTorch required                    ║
║  ✅ CPU optimized & parallel training                     ║
║                                                           ║
║  Quick Start:                                             ║
║    import naply                                           ║
║    model = naply.Model("medium")                          ║
║    model.train("my_data/", epochs=10)                     ║
║    model.chat("Hello!")                                   ║
╚═══════════════════════════════════════════════════════════╝
""")


def cmd_methods():
    """List available training methods."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                   NAPLY Training Methods                  ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  CRC  - Consistency-Retention Compression                 ║
║         Memory-efficient gradient compression             ║
║                                                           ║
║  DCL  - Domain-Constrained Learning                       ║
║         Freeze layers for domain-specific training        ║
║                                                           ║
║  ILC  - Incremental Learning Consolidation                ║
║         Prevent catastrophic forgetting                   ║
║                                                           ║
║  MCU  - Memory Consolidation Unit                         ║
║         Stable knowledge merging with EMA                 ║
║                                                           ║
║  P3   - Parallel Pipelined Processing                     ║
║         Gradient accumulation for large batches           ║
║                                                           ║
║  PPL  - Progressive Prompt Learning                       ║
║         Curriculum learning (easy → hard)                 ║
║                                                           ║
║  PTL  - Parallel Training and Learning                    ║
║         Multi-threaded CPU training for speed            ║
║                                                           ║
║  RDL  - Recursive Data Learning                           ║
║         Reasoning state consistency                       ║
║                                                           ║
║  S3L  - Structured Selective Stabilized Learning          ║
║         Unified training with confidence gating           ║
║                                                           ║
║  SGL  - Sparse Gradient Learning                          ║
║         Efficient sparse gradient updates                 ║
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║  Usage:                                                   ║
║    from naply import Model, S3LTrainer                    ║
║    model = Model("medium")                                ║
║    trainer = S3LTrainer(model.model)                      ║
║    trainer.train(dataloader, epochs=10)                   ║
╚═══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
