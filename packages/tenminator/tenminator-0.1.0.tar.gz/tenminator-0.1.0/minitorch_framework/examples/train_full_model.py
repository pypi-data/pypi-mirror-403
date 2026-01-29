_**```python
import numpy as np
import sys
sys.path.insert(0, ".")
sys.path.insert(0, "..")

from minitorch_lite import Tensor, nn, optim
from minitorch_lite.training import TrainingController
from minitorch_framework.models.transformer_rlm import TransformerRLM

def main():
    """Función principal para el entrenamiento del modelo."""
    # 1. Configuración del Modelo
    vocab_size = 1000
    d_model = 128
    nhead = 4
    num_layers = 2
    d_ff = 256

    # 2. Creación del Modelo
    model = TransformerRLM(vocab_size, d_model, nhead, num_layers, d_ff)

    # 3. Creación de Datos Falsos
    batch_size = 8
    seq_len = 32
    train_data = np.random.randint(0, vocab_size, size=(100, seq_len))
    train_labels = np.random.randint(0, vocab_size, size=(100, seq_len))

    # 4. Creación del Optimizador y la Función de Pérdida
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.CrossEntropyLoss()

    # 5. Creación del Controlador de Entrenamiento
    controller = TrainingController(model, optimizer, loss_fn)

    # 6. Entrenamiento del Modelo
    print("Iniciando entrenamiento...")
    controller.train(train_data, train_labels, epochs=5, batch_size=batch_size)
    print("Entrenamiento completado.")

    # 7. Ejemplo de Inferencia
    print("\nEjemplo de inferencia:")
    input_sentence = np.random.randint(0, vocab_size, size=(1, 10))
    output = model(input_sentence)
    print(f"Forma de la salida: {output.shape}")

if __name__ == "__main__":
    main()
```**_
