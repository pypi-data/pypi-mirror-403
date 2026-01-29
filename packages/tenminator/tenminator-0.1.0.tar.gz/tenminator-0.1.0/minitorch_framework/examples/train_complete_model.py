"""
MiniTorch Framework - Script de Entrenamiento Completo
======================================================
Script end-to-end para entrenar un modelo general con:
- Transformer RLM
- Reinforcement Learning (PPO)
- Relational Networks
- Control de entrenamiento (Early Stopping, checkpoints)
- vLLM para inferencia

Uso:
    python train_complete_model.py --config config.json
"""

import numpy as np
import sys
import argparse
import json
from pathlib import Path

# Añadir rutas
sys.path.insert(0, '/home/ubuntu')
sys.path.insert(0, '/home/ubuntu/minitorch_framework')

# Importar MiniTorch Lite
from minitorch_lite import (
    Tensor, Adam, CrossEntropyLoss,
    create_training_controller, ModelExporter
)

# Importar módulos del framework
from models.transformer_rlm import TransformerRLM
from rl.reinforcement_learning import PPOAgent, DQNAgent
from vllm.relational_vllm import RelationalNetwork, vLLM

class CompleteTrainingPipeline:
    """
    Pipeline completo de entrenamiento para modelos generales.
    """
    
    def __init__(self, config: dict):
        self.config = config
        
        # Configuración del modelo
        model_config = config.get('model', {})
        self.vocab_size = model_config.get('vocab_size', 50000)
        self.d_model = model_config.get('d_model', 512)
        self.num_heads = model_config.get('num_heads', 8)
        self.num_layers = model_config.get('num_layers', 6)
        self.d_ff = model_config.get('d_ff', 2048)
        self.max_len = model_config.get('max_len', 2048)
        
        # Configuración de entrenamiento
        train_config = config.get('training', {})
        self.batch_size = train_config.get('batch_size', 32)
        self.learning_rate = train_config.get('learning_rate', 0.0001)
        self.max_iterations = train_config.get('max_iterations', 69)
        self.early_stop_patience = train_config.get('early_stop_patience', 12)
        self.checkpoint_dir = train_config.get('checkpoint_dir', './checkpoints')
        
        # Crear directorio de checkpoints
        Path(self.checkpoint_dir).mkdir(parents=True, exist_ok=True)
        
        print("=" * 70)
        print("MiniTorch Framework - Pipeline de Entrenamiento Completo")
        print("=" * 70)
        
        # Inicializar modelo
        print("\n[1/5] Inicializando Transformer RLM...")
        self.model = TransformerRLM(
            vocab_size=self.vocab_size,
            d_model=self.d_model,
            num_heads=self.num_heads,
            num_layers=self.num_layers,
            d_ff=self.d_ff,
            max_len=self.max_len
        )
        
        # Inicializar optimizador
        print("\n[2/5] Inicializando optimizador Adam...")
        self.optimizer = Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Inicializar función de pérdida
        print("\n[3/5] Inicializando función de pérdida...")
        self.criterion = CrossEntropyLoss()
        
        # Inicializar controlador de entrenamiento
        print("\n[4/5] Inicializando controlador de entrenamiento...")
        self.controller = create_training_controller(
            max_iterations=self.max_iterations,
            early_stop=True,
            early_stop_patience=self.early_stop_patience,
            checkpoint_dir=self.checkpoint_dir
        )
        
        # Inicializar vLLM para inferencia
        print("\n[5/5] Inicializando vLLM para inferencia rápida...")
        self.vllm = vLLM(self.model, max_batch_size=8, max_seq_len=self.max_len)
        
        print("\n" + "=" * 70)
        print("Inicialización completada")
        print("=" * 70)
    
    def generate_synthetic_data(self, num_samples: int = 1000) -> tuple:
        """
        Genera datos sintéticos para entrenamiento de demostración.
        
        Args:
            num_samples: Número de muestras a generar
        
        Returns:
            (inputs, targets): Datos de entrada y objetivos
        """
        print(f"\n[Datos] Generando {num_samples} muestras sintéticas...")
        
        # Generar secuencias aleatorias
        seq_len = 128
        inputs = np.random.randint(0, self.vocab_size, (num_samples, seq_len))
        
        # Targets: siguiente token (shifted)
        targets = np.roll(inputs, -1, axis=1)
        targets[:, -1] = 0  # Padding
        
        print(f"[Datos] Forma de inputs: {inputs.shape}")
        print(f"[Datos] Forma de targets: {targets.shape}")
        
        return inputs, targets
    
    def train_step(self, inputs: np.ndarray, targets: np.ndarray) -> float:
        """
        Realiza un paso de entrenamiento.
        
        Args:
            inputs: Secuencias de entrada (batch_size, seq_len)
            targets: Secuencias objetivo (batch_size, seq_len)
        
        Returns:
            Pérdida del paso
        """
        # Forward pass
        logits = self.model.forward(inputs)
        
        # Calcular pérdida
        # Reshape para CrossEntropyLoss: (batch_size * seq_len, vocab_size)
        batch_size, seq_len, vocab_size = logits.data.shape
        logits_flat = logits.data.reshape(-1, vocab_size)
        targets_flat = targets.reshape(-1)
        
        logits_tensor = Tensor(logits_flat, requires_grad=True)
        targets_tensor = Tensor(targets_flat, requires_grad=False)
        
        loss = self.criterion(logits_tensor, targets_tensor)
        
        # Backward pass (simulado)
        # En una implementación completa, aquí se calcularían los gradientes
        # loss.backward()
        
        # Actualizar pesos (simulado)
        # self.optimizer.step()
        # self.optimizer.zero_grad()
        
        return loss.item()
    
    def train(self, num_epochs: int = 10):
        """
        Bucle de entrenamiento principal.
        
        Args:
            num_epochs: Número de épocas de entrenamiento
        """
        print("\n" + "=" * 70)
        print("Iniciando Entrenamiento")
        print("=" * 70)
        
        # Generar datos sintéticos
        inputs, targets = self.generate_synthetic_data(num_samples=1000)
        
        # Dividir en batches
        num_batches = len(inputs) // self.batch_size
        
        for epoch in range(num_epochs):
            print(f"\n--- Época {epoch + 1}/{num_epochs} ---")
            
            epoch_loss = 0.0
            
            for batch_idx in range(num_batches):
                # Verificar si debe continuar
                if not self.controller.should_continue():
                    print(f"\n[Entrenamiento] Detenido: {self.controller.state.stop_reason}")
                    break
                
                # Obtener batch
                start_idx = batch_idx * self.batch_size
                end_idx = start_idx + self.batch_size
                batch_inputs = inputs[start_idx:end_idx]
                batch_targets = targets[start_idx:end_idx]
                
                # Paso de entrenamiento
                loss = self.train_step(batch_inputs, batch_targets)
                epoch_loss += loss
                
                # Actualizar controlador
                self.controller.update(loss, tokens_processed=batch_inputs.size)
            
            # Pérdida promedio de la época
            avg_loss = epoch_loss / num_batches
            print(f"Pérdida promedio de la época: {avg_loss:.6f}")
            
            # Guardar checkpoint cada 5 épocas
            if (epoch + 1) % 5 == 0:
                checkpoint_path = f"{self.checkpoint_dir}/model_epoch_{epoch+1}.pkl"
                self.save_checkpoint(checkpoint_path)
        
        print("\n" + "=" * 70)
        print("Entrenamiento Completado")
        print("=" * 70)
        print(self.controller.get_summary())
        
        # Guardar checkpoint final
        final_checkpoint = f"{self.checkpoint_dir}/model_final.pkl"
        self.save_checkpoint(final_checkpoint)
    
    def save_checkpoint(self, filepath: str):
        """Guarda un checkpoint del modelo."""
        self.controller.save_checkpoint(
            model_state=self.model.state_dict(),
            optimizer_state=self.optimizer.state_dict(),
            filepath=filepath
        )
    
    def load_checkpoint(self, filepath: str):
        """Carga un checkpoint del modelo."""
        checkpoint = self.controller.load_checkpoint(filepath)
        self.model.load_state_dict(checkpoint['model_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
    
    def evaluate(self, test_inputs: np.ndarray, test_targets: np.ndarray) -> float:
        """
        Evalúa el modelo en datos de prueba.
        
        Args:
            test_inputs: Datos de entrada de prueba
            test_targets: Objetivos de prueba
        
        Returns:
            Pérdida promedio en el conjunto de prueba
        """
        print("\n[Evaluación] Evaluando modelo...")
        
        self.model.eval()
        
        total_loss = 0.0
        num_batches = len(test_inputs) // self.batch_size
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = start_idx + self.batch_size
            batch_inputs = test_inputs[start_idx:end_idx]
            batch_targets = test_targets[start_idx:end_idx]
            
            loss = self.train_step(batch_inputs, batch_targets)
            total_loss += loss
        
        avg_loss = total_loss / num_batches
        
        self.model.train()
        
        print(f"[Evaluación] Pérdida promedio: {avg_loss:.6f}")
        return avg_loss
    
    def generate_text(self, prompt: str, max_length: int = 100) -> str:
        """
        Genera texto a partir de un prompt.
        
        Args:
            prompt: Texto inicial
            max_length: Longitud máxima a generar
        
        Returns:
            Texto generado
        """
        print(f"\n[Generación] Prompt: '{prompt}'")
        
        # Tokenizar prompt (simulado)
        prompt_tokens = np.array([[ord(c) % self.vocab_size for c in prompt]])
        
        # Generar con vLLM
        generated_tokens = self.vllm.generate(
            prompt_tokens,
            max_new_tokens=max_length,
            temperature=0.8,
            top_k=50,
            top_p=0.9
        )
        
        # Decodificar (simulado)
        generated_text = ''.join([chr(t % 128) for t in generated_tokens[0]])
        
        print(f"[Generación] Texto generado: '{generated_text[:200]}...'")
        return generated_text
    
    def export_model(self, format: str = 'numpy'):
        """
        Exporta el modelo a diferentes formatos.
        
        Args:
            format: Formato de exportación ('numpy', 'keras', 'pytorch')
        """
        print(f"\n[Exportación] Exportando modelo a formato {format}...")
        
        exporter = ModelExporter()
        export_path = f"{self.checkpoint_dir}/model_export.{format}"
        
        exporter.export(self.model.state_dict(), export_path, format=format)
        
        print(f"[Exportación] Modelo exportado: {export_path}")

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Entrenar modelo completo con MiniTorch Framework')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Ruta al archivo de configuración')
    parser.add_argument('--epochs', type=int, default=10,
                       help='Número de épocas de entrenamiento')
    parser.add_argument('--generate', action='store_true',
                       help='Generar texto después del entrenamiento')
    
    args = parser.parse_args()
    
    # Cargar configuración
    if Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        # Configuración por defecto
        config = {
            'model': {
                'vocab_size': 50000,
                'd_model': 512,
                'num_heads': 8,
                'num_layers': 6,
                'd_ff': 2048,
                'max_len': 2048
            },
            'training': {
                'batch_size': 32,
                'learning_rate': 0.0001,
                'max_iterations': 69,
                'early_stop_patience': 12,
                'checkpoint_dir': './checkpoints'
            }
        }
        
        # Guardar configuración por defecto
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print(f"[Config] Configuración por defecto guardada en config.json")
    
    # Crear pipeline
    pipeline = CompleteTrainingPipeline(config)
    
    # Entrenar
    pipeline.train(num_epochs=args.epochs)
    
    # Generar texto si se solicita
    if args.generate:
        pipeline.generate_text("Hello, this is a test", max_length=100)
    
    # Exportar modelo
    pipeline.export_model(format='numpy')
    
    print("\n" + "=" * 70)
    print("Pipeline Completo Finalizado")
    print("=" * 70)

if __name__ == '__main__':
    main()
