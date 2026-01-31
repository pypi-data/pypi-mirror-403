"""
NAPLY Easy API - Simplest Way to Build AI Models
=================================================

Just a few lines of code to build powerful AI models!

Example:
    import naply.easy as ai
    
    # Train AI (3 lines!)
    model = ai.train("my_data/", epochs=5)
    
    # Chat (1 line!)
    response = ai.chat("Hello!")
"""

import os
from typing import Optional, Union
from .model import Model
from .config import get_preset


def train(
    data_path: str,
    output: str = "my_ai_model",
    size: str = "small",
    epochs: int = 5,
    **kwargs
) -> Model:
    """
    Train an AI model in just 1 line!
    
    Args:
        data_path: Path to your training data (folder, .txt, .json, .jsonl, .csv)
        output: Where to save the model (default: "my_ai_model")
        size: Model size - "tiny", "small", "medium", "large", "xl" (default: "small")
        epochs: Number of training epochs (default: 5)
        **kwargs: Additional training options
    
    Returns:
        Trained Model instance
    
    Example:
        # Super simple - just 1 line!
        model = naply.easy.train("my_data/", epochs=10)
        
        # With options
        model = naply.easy.train(
            "my_data/",
            size="medium",
            epochs=15,
            batch_size=32
        )
    """
    print("🚀 Training your AI model...")
    print(f"   Data: {data_path}")
    print(f"   Size: {size}")
    print(f"   Epochs: {epochs}")
    print()
    
    # Create model
    model = Model(size, **kwargs)
    
    # Train
    model.train(
        data_path=data_path,
        epochs=epochs,
        output_dir=output,
        verbose=True,
        **{k: v for k, v in kwargs.items() if k not in ['size', 'epochs', 'output']}
    )
    
    print()
    print("✅ Training complete!")
    print(f"📁 Model saved to: {output}/")
    print()
    print("💬 Chat with your AI:")
    print(f"   import naply.easy as ai")
    print(f"   ai.chat('Hello!')")
    
    return model


def chat(
    model_path: Optional[str] = None,
    prompt: str = None,
    model: Optional[Model] = None
) -> str:
    """
    Chat with your AI model in just 1 line!
    
    Args:
        model_path: Path to trained model (if None, uses default "my_ai_model")
        prompt: Your question/prompt
        model: Pre-loaded Model instance (optional)
    
    Returns:
        AI response
    
    Example:
        # Simple chat
        response = naply.easy.chat("Hello! How are you?")
        
        # With custom model
        response = naply.easy.chat(
            model_path="my_model/",
            prompt="Explain machine learning"
        )
    """
    # Load model if needed
    if model is None:
        if model_path is None:
            model_path = "my_ai_model"
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at '{model_path}'. "
                f"Train a model first with: naply.easy.train('your_data/')"
            )
        
        model = Model.load(model_path)
    
    # Interactive mode if no prompt
    if prompt is None:
        return _interactive_chat(model)
    
    # Single prompt mode
    response = model.chat(prompt)
    return response


def _interactive_chat(model: Model):
    """Interactive chat mode."""
    print("=" * 60)
    print("🤖 NAPLY AI Chat - Interactive Mode")
    print("=" * 60)
    print("   Type 'quit' to exit")
    print("-" * 60)
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("AI: ", end="", flush=True)
            response = model.chat(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
    
    return ""


def build(
    size: str = "small",
    layers: Optional[int] = None,
    heads: Optional[int] = None,
    embedding: Optional[int] = None,
    **kwargs
) -> Model:
    """
    Build an AI model in just 1 line!
    
    Args:
        size: Model size preset - "tiny", "small", "medium", "large", "xl", "xxl"
        layers: Custom number of layers (optional)
        heads: Custom number of attention heads (optional)
        embedding: Custom embedding dimension (optional)
        **kwargs: Additional model options
    
    Returns:
        Model instance
    
    Example:
        # Quick preset
        model = naply.easy.build("medium")
        
        # Custom architecture
        model = naply.easy.build(
            layers=24,
            heads=16,
            embedding=1024
        )
    """
    if layers or heads or embedding:
        # Custom architecture
        model = Model(
            layers=layers or 12,
            heads=heads or 12,
            embedding=embedding or 768,
            **kwargs
        )
    else:
        # Use preset
        model = Model(size, **kwargs)
    
    print("✅ AI model created!")
    print(model.summary())
    
    return model


def quick_start(data_path: str, epochs: int = 5):
    """
    Quick start - train and chat in 2 lines!
    
    Args:
        data_path: Path to training data
        epochs: Number of epochs
    
    Example:
        # Train and chat in 2 lines!
        naply.easy.quick_start("my_data/", epochs=10)
        naply.easy.chat("Hello!")
    """
    # Train
    model = train(data_path, epochs=epochs)
    
    # Start interactive chat
    print()
    print("=" * 60)
    print("🎉 Your AI is ready! Starting chat...")
    print("=" * 60)
    print()
    
    _interactive_chat(model)


# Export main functions
__all__ = ['train', 'chat', 'build', 'quick_start']
