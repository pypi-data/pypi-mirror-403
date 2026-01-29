
import numpy as np
import sys
sys.path.insert(0, ".")
sys.path.insert(0, "..")

from minitorch_lite import Tensor, nn, optim
from minitorch_lite.training import TrainingController

def test_early_stopping():
    """Prueba el sistema de early stopping (12 iteraciones sin mejora)."""
    print("\n--- Probando Early Stopping ---")
    model = nn.Linear(10, 1)
    optimizer = optim.SGD(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()
    controller = TrainingController(model, optimizer, loss_fn, early_stop_patience=12)

    # Simular 20 iteraciones donde la pérdida no mejora
    for i in range(20):
        if not controller.should_continue():
            print(f"Entrenamiento detenido en la iteración {i} por early stopping.")
            break
        # Simular una pérdida constante
        controller.update(loss=1.0)

    assert i == 13, "El early stopping no se activó en la iteración 13."
    print("Prueba de Early Stopping completada con éxito.")

def test_max_iterations():
    """Prueba el límite máximo de 69 iteraciones."""
    print("\n--- Probando Límite Máximo de Iteraciones ---")
    from minitorch_lite.training import TrainingConfig
    config = TrainingConfig(max_iterations=69, early_stop_patience=100)
    controller = TrainingController(None, None, None, config=config)

    # Simular 100 iteraciones
    for i in range(100):
        if not controller.should_continue():
            print(f"Entrenamiento detenido en la iteración {i} por límite máximo.")
            break
        controller.update(loss=1.0)

    assert i == 69, "El límite máximo de iteraciones no se activó en la iteración 69."
    print("Prueba de Límite Máximo de Iteraciones completada con éxito.")

def main():
    test_early_stopping()
    test_max_iterations()

if __name__ == "__main__":
    main()

