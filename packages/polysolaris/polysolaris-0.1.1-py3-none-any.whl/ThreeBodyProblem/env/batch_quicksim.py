import torch
class FastBatchSimulation:
    def __init__(self, masses, initial_position: torch.tensor, initial_velocity, batch_size=1):
        self.masses=masses.view(1, -1, 1).expand(batch_size, -1, -1) #(1, N, 1)
        self.pos=initial_position #(N, N)
        self.v=initial_velocity#(N, N)
        self.initial_position = initial_position.clone() 
        self.initial_velocity = initial_velocity.clone()
        self.pos = self.initial_position.clone()
        self.v = self.initial_velocity.clone()
        self.G = 1
    def step(self, dt):
        pos_i = self.pos.unsqueeze(2)
        pos_j = self.pos.unsqueeze(1)
        diff = pos_i-pos_j
        sq_diff = diff.pow(2)
        dist_sq = sq_diff.sum(dim=-1, keepdim=True)
        dist = torch.sqrt(dist_sq+1e-9)

        mass_j = self.masses.unsqueeze(1)
        force_mag = (self.G*mass_j)/dist.pow(3)

        acceleration = diff*force_mag
        net_acc = acceleration.sum(dim=2)

        self.v += net_acc*dt
        self.pos += self.v*dt
        return self.pos, self.v
    def reset(self, new_pos=None, new_v=None):
        if new_pos is not None:
            self.pos = new_pos
            self.v = new_v
        else:
            self.pos = self.initial_position.clone()
            self.v = self.initial_velocity.clone()
        return self.pos, self.v

