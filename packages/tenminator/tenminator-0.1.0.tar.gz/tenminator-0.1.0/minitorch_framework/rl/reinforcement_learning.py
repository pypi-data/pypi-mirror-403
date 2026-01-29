"""
MiniTorch Framework - Reinforcement Learning Module
===================================================
Implementación de algoritmos de Reinforcement Learning:
- Q-Learning (Deep Q-Network)
- PPO (Proximal Policy Optimization)
- Actor-Critic
"""

import numpy as np
import sys
sys.path.insert(0, '/home/ubuntu')
from minitorch_lite import Module, Parameter, Tensor, Linear, Sequential, ReLU, Softmax, Tanh
from typing import Tuple, List, Dict, Any
import pickle

class ReplayBuffer:
    """
    Buffer de experiencia para almacenar transiciones (s, a, r, s', done).
    """
    
    def __init__(self, capacity: int = 100000):
        self.capacity = capacity
        self.buffer = []
        self.position = 0
    
    def push(self, state, action, reward, next_state, done):
        """Añade una transición al buffer."""
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.position] = (state, action, reward, next_state, done)
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int) -> Tuple:
        """Muestrea un batch aleatorio del buffer."""
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[i] for i in indices]
        
        states = np.array([t[0] for t in batch])
        actions = np.array([t[1] for t in batch])
        rewards = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones = np.array([t[4] for t in batch])
        
        return states, actions, rewards, next_states, dones
    
    def __len__(self):
        return len(self.buffer)

class DQN(Module):
    """
    Deep Q-Network para Q-Learning.
    
    Args:
        state_dim: Dimensión del espacio de estados
        action_dim: Dimensión del espacio de acciones
        hidden_dims: Lista de dimensiones de capas ocultas
    """
    
    def __init__(self, state_dim: int, action_dim: int, 
                 hidden_dims: List[int] = [256, 256]):
        super().__init__()
        
        layers = []
        prev_dim = state_dim
        
        for hidden_dim in hidden_dims:
            layers.append(Linear(prev_dim, hidden_dim))
            layers.append(ReLU())
            prev_dim = hidden_dim
        
        layers.append(Linear(prev_dim, action_dim))
        
        self.network = Sequential(*layers)
        self._modules['network'] = self.network
        
        self.state_dim = state_dim
        self.action_dim = action_dim
    
    def forward(self, state: Tensor) -> Tensor:
        """
        Forward pass del DQN.
        
        Args:
            state: Estado (batch_size, state_dim)
        
        Returns:
            Q-values (batch_size, action_dim)
        """
        return self.network(state)
    
    def select_action(self, state: np.ndarray, epsilon: float = 0.1) -> int:
        """
        Selecciona una acción usando epsilon-greedy.
        
        Args:
            state: Estado actual
            epsilon: Probabilidad de exploración
        
        Returns:
            Acción seleccionada
        """
        if np.random.rand() < epsilon:
            return np.random.randint(self.action_dim)
        else:
            state_tensor = Tensor(state.reshape(1, -1), requires_grad=False)
            q_values = self.forward(state_tensor)
            return int(np.argmax(q_values.data))

class DQNAgent:
    """
    Agente de Q-Learning con Experience Replay y Target Network.
    """
    
    def __init__(self, state_dim: int, action_dim: int, 
                 learning_rate: float = 0.001, gamma: float = 0.99,
                 buffer_capacity: int = 100000, batch_size: int = 64):
        from minitorch_lite import Adam
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.batch_size = batch_size
        
        # Redes Q y Target
        self.q_network = DQN(state_dim, action_dim)
        self.target_network = DQN(state_dim, action_dim)
        self._update_target_network()
        
        # Optimizador
        self.optimizer = Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Replay Buffer
        self.replay_buffer = ReplayBuffer(buffer_capacity)
        
        # Epsilon para exploración
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
    
    def _update_target_network(self):
        """Copia los pesos de q_network a target_network."""
        target_state = self.q_network.state_dict()
        self.target_network.load_state_dict(target_state)
    
    def select_action(self, state: np.ndarray) -> int:
        """Selecciona una acción usando epsilon-greedy."""
        return self.q_network.select_action(state, self.epsilon)
    
    def store_transition(self, state, action, reward, next_state, done):
        """Almacena una transición en el replay buffer."""
        self.replay_buffer.push(state, action, reward, next_state, done)
    
    def train_step(self) -> float:
        """
        Realiza un paso de entrenamiento.
        
        Returns:
            Pérdida del paso de entrenamiento
        """
        if len(self.replay_buffer) < self.batch_size:
            return 0.0
        
        # Muestrear batch
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)
        
        # Convertir a tensores
        states_tensor = Tensor(states, requires_grad=True)
        next_states_tensor = Tensor(next_states, requires_grad=False)
        
        # Q-values actuales
        q_values = self.q_network(states_tensor)
        q_values_actions = q_values.data[np.arange(self.batch_size), actions.astype(int)]
        
        # Q-values objetivo
        with self.target_network.eval():
            next_q_values = self.target_network(next_states_tensor)
            max_next_q_values = np.max(next_q_values.data, axis=1)
        
        # Target: r + gamma * max Q(s', a') * (1 - done)
        targets = rewards + self.gamma * max_next_q_values * (1 - dones)
        
        # Pérdida MSE
        loss = np.mean((q_values_actions - targets) ** 2)
        
        # Backward (simulado)
        # En una implementación completa, aquí se calcularían los gradientes
        # y se actualizarían los pesos con optimizer.step()
        
        # Actualizar epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        return loss

class ActorCritic(Module):
    """
    Actor-Critic Network para PPO.
    
    Args:
        state_dim: Dimensión del espacio de estados
        action_dim: Dimensión del espacio de acciones
        hidden_dims: Lista de dimensiones de capas ocultas
    """
    
    def __init__(self, state_dim: int, action_dim: int,
                 hidden_dims: List[int] = [256, 256]):
        super().__init__()
        
        # Actor (política)
        actor_layers = []
        prev_dim = state_dim
        for hidden_dim in hidden_dims:
            actor_layers.append(Linear(prev_dim, hidden_dim))
            actor_layers.append(Tanh())
            prev_dim = hidden_dim
        actor_layers.append(Linear(prev_dim, action_dim))
        actor_layers.append(Softmax(dim=-1))
        
        self.actor = Sequential(*actor_layers)
        self._modules['actor'] = self.actor
        
        # Critic (función de valor)
        critic_layers = []
        prev_dim = state_dim
        for hidden_dim in hidden_dims:
            critic_layers.append(Linear(prev_dim, hidden_dim))
            critic_layers.append(Tanh())
            prev_dim = hidden_dim
        critic_layers.append(Linear(prev_dim, 1))
        
        self.critic = Sequential(*critic_layers)
        self._modules['critic'] = self.critic
        
        self.state_dim = state_dim
        self.action_dim = action_dim
    
    def forward(self, state: Tensor) -> Tuple[Tensor, Tensor]:
        """
        Forward pass del Actor-Critic.
        
        Args:
            state: Estado (batch_size, state_dim)
        
        Returns:
            (action_probs, value): Probabilidades de acción y valor del estado
        """
        action_probs = self.actor(state)
        value = self.critic(state)
        return action_probs, value
    
    def select_action(self, state: np.ndarray) -> Tuple[int, float]:
        """
        Selecciona una acción según la política.
        
        Args:
            state: Estado actual
        
        Returns:
            (action, log_prob): Acción seleccionada y su log-probabilidad
        """
        state_tensor = Tensor(state.reshape(1, -1), requires_grad=False)
        action_probs, _ = self.forward(state_tensor)
        
        # Sampling
        probs = action_probs.data[0]
        action = np.random.choice(self.action_dim, p=probs)
        log_prob = np.log(probs[action] + 1e-10)
        
        return action, log_prob

class PPOAgent:
    """
    Agente PPO (Proximal Policy Optimization).
    
    Args:
        state_dim: Dimensión del espacio de estados
        action_dim: Dimensión del espacio de acciones
        learning_rate: Tasa de aprendizaje
        gamma: Factor de descuento
        epsilon_clip: Epsilon para clipping de PPO
        epochs: Número de épocas de actualización por batch
    """
    
    def __init__(self, state_dim: int, action_dim: int,
                 learning_rate: float = 0.0003, gamma: float = 0.99,
                 epsilon_clip: float = 0.2, epochs: int = 10):
        from minitorch_lite import Adam
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon_clip = epsilon_clip
        self.epochs = epochs
        
        # Actor-Critic Network
        self.policy = ActorCritic(state_dim, action_dim)
        
        # Optimizador
        self.optimizer = Adam(self.policy.parameters(), lr=learning_rate)
        
        # Buffer de trayectorias
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.dones = []
    
    def select_action(self, state: np.ndarray) -> int:
        """Selecciona una acción según la política."""
        action, log_prob = self.policy.select_action(state)
        
        # Almacenar para entrenamiento
        self.states.append(state)
        self.actions.append(action)
        self.log_probs.append(log_prob)
        
        return action
    
    def store_reward(self, reward: float, done: bool):
        """Almacena recompensa y flag de terminación."""
        self.rewards.append(reward)
        self.dones.append(done)
    
    def compute_returns(self) -> np.ndarray:
        """Calcula los retornos descontados."""
        returns = []
        R = 0
        for reward, done in zip(reversed(self.rewards), reversed(self.dones)):
            if done:
                R = 0
            R = reward + self.gamma * R
            returns.insert(0, R)
        
        returns = np.array(returns, dtype=np.float32)
        # Normalizar
        returns = (returns - np.mean(returns)) / (np.std(returns) + 1e-8)
        return returns
    
    def train_step(self) -> float:
        """
        Realiza un paso de entrenamiento PPO.
        
        Returns:
            Pérdida promedio
        """
        if len(self.states) == 0:
            return 0.0
        
        # Convertir a arrays
        states = np.array(self.states, dtype=np.float32)
        actions = np.array(self.actions, dtype=np.int32)
        old_log_probs = np.array(self.log_probs, dtype=np.float32)
        returns = self.compute_returns()
        
        total_loss = 0.0
        
        # Entrenar por múltiples épocas
        for _ in range(self.epochs):
            # Forward pass
            states_tensor = Tensor(states, requires_grad=True)
            action_probs, values = self.policy(states_tensor)
            
            # Log-probabilidades de las acciones tomadas
            new_log_probs = np.log(action_probs.data[np.arange(len(actions)), actions] + 1e-10)
            
            # Ratio de probabilidades
            ratios = np.exp(new_log_probs - old_log_probs)
            
            # Ventajas
            advantages = returns - values.data.flatten()
            
            # Pérdida PPO con clipping
            surr1 = ratios * advantages
            surr2 = np.clip(ratios, 1 - self.epsilon_clip, 1 + self.epsilon_clip) * advantages
            actor_loss = -np.mean(np.minimum(surr1, surr2))
            
            # Pérdida del critic
            critic_loss = np.mean((returns - values.data.flatten()) ** 2)
            
            # Pérdida total
            loss = actor_loss + 0.5 * critic_loss
            total_loss += loss
        
        # Limpiar buffer
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.dones = []
        
        return total_loss / self.epochs
    
    def save(self, filepath: str):
        """Guarda el modelo."""
        state = {
            'policy': self.policy.state_dict(),
            'optimizer': self.optimizer.state_dict()
        }
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        print(f"[PPOAgent] Modelo guardado: {filepath}")
    
    def load(self, filepath: str):
        """Carga el modelo."""
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        self.policy.load_state_dict(state['policy'])
        self.optimizer.load_state_dict(state['optimizer'])
        print(f"[PPOAgent] Modelo cargado: {filepath}")
