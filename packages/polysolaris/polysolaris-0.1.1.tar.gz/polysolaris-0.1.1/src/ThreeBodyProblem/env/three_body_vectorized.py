import torch
from .batch_quicksim import FastBatchSimulation
# import torch._dynamo
class VectorizedThreeBodyEnv:
    def __init__(self, num_envs, device='cuda'):
        self.num_envs = num_envs
        self.device = device
        self.masses = torch.tensor([1, 1, 1], dtype=torch.float32).to(device)
        
        init_pos = torch.randn(num_envs, 3, 3).to(device)*5.0
        init_v = torch.randn(num_envs, 3, 3).to(device)
    
        self.sim = FastBatchSimulation(self.masses, init_pos, init_v, batch_size=self.num_envs)
        self.total_rewards = torch.zeros(self.num_envs, device=self.device)
        self.active_mask = torch.ones(self.num_envs, dtype=torch.bool, device=self.device)
        self.steps_alive = torch.zeros(self.num_envs, device=self.device)
        self.max_step = 3000
    
    def _get_obs(self):
        pos = self.sim.pos
        vel = self.sim.v
        mass = self.sim.masses

        m1, m2, m3 = mass[:, 0], mass[:, 1], mass[:, 2]
        rel_pos12 = pos[:, 0] - pos[:, 1]
        rel_pos23 = pos[:, 1] - pos[:, 2]
        rel_pos31 = pos[:, 2] - pos[:, 0]
        
        eps = 1e-6
        dist12 = rel_pos12.norm(dim=1, keepdim=True) + eps
        dist23 = rel_pos23.norm(dim=1, keepdim=True) + eps
        dist31 = rel_pos31.norm(dim=1, keepdim=True) + eps

        d12_cubed = (rel_pos12.norm(dim=1, keepdim=True) + eps).pow(3)
        d23_cubed = (rel_pos23.norm(dim=1, keepdim=True) + eps).pow(3)
        d31_cubed = (rel_pos31.norm(dim=1, keepdim=True) + eps).pow(3)

        a1 = -m2*(rel_pos12)/(d12_cubed) + m3*rel_pos31/(d31_cubed)
        a2 = -m3*(rel_pos23)/(d23_cubed) + m1*rel_pos12/(d12_cubed)
        a3 = -m1*(rel_pos31)/(d31_cubed) + m2*rel_pos23/(d23_cubed)

        flat_rel_pos = torch.cat([rel_pos12, rel_pos23, rel_pos31], dim=1)
        flat_v = vel.reshape(self.num_envs, -1)
        flat_m = mass.squeeze(2).reshape(self.num_envs, -1)

        flat_accel = torch.tanh(torch.cat([a1, a2, a3], dim=1))
        
        u1 = - (m2 / rel_pos12) - (m3 / rel_pos31)
        u2 = - (m1 / rel_pos12) - (m3 / rel_pos23)
        u3 = - (m3 / rel_pos31) - (m2 / rel_pos23)

        flat_potential = torch.tanh(torch.cat([u1, u2, u3], dim=1))

        u12 = rel_pos12/dist12
        u23 = rel_pos23/dist23
        u31 = rel_pos31/dist31
        cos_1 = (u12*(-u31)).sum(dim=1, keepdim=True)
        cos_2 = (u23*(-u12)).sum(dim=1, keepdim=True)
        cos_3 = (u23*(-u12)).sum(dim=1, keepdim=True)
        flat_angles = torch.cat([cos_1, cos_2, cos_3], dim=1)

        return torch.cat([
            flat_rel_pos,  #9
            flat_v,        #9
            flat_m,        #3
            flat_accel,    #9 
            flat_potential,#3
            flat_angles    #3
            ], dim=1)
    
    def step(self, actions):
            new_v = actions.view(self.num_envs, 3, 3)
            self.sim.v = new_v
            
            self.total_rewards.fill_(0)
            self.steps_alive.fill_(0)
            self.active_mask.fill_(True)
            
            T = self.max_step + 500
            dt = 5e-3
            check_interval = 100
            
            r_survival = 0.01
            r_sweet = 0.01
            r_collision = -0.05
            r_escape = 0
            r_toofar = -10.0 / T
            
            for t in range(T):
                if t % check_interval == 0:
                    if not self.active_mask.any():
                        break
                
                pos, v = self.sim.step(dt)
                active_f = self.active_mask.float()
                
                self.steps_alive += active_f
                self.total_rewards += r_survival * active_f

                p1, p2, p3 = pos[:, 0], pos[:, 1], pos[:, 2]
                
                d12 = (p1 - p2).norm(dim=1)
                d23 = (p2 - p3).norm(dim=1)
                d13 = (p1 - p3).norm(dim=1)
                
                rel_dists = torch.stack([d12, d23, d13], dim=1)
                min_rel_dist, _ = rel_dists.min(dim=1)
                max_rel_dist, _ = rel_dists.max(dim=1)
                

                r1 = p1.norm(dim=1)
                r2 = p2.norm(dim=1)
                r3 = p3.norm(dim=1)
                
                origin_dists = torch.stack([r1, r2, r3], dim=1)
                max_dist_origin, _ = origin_dists.max(dim=1)

                
                collision_mask = min_rel_dist < 0.025
                escaped_mask = (max_rel_dist > 50) | (max_dist_origin > 50)
                too_far_mask = (max_rel_dist > 30) | (max_dist_origin > 30)
                sweet_spot_mask = (max_rel_dist > 1) & (max_rel_dist < 10) & (max_dist_origin < 10)
            
                self.total_rewards += r_collision * collision_mask.float() * active_f

                valid_escape = escaped_mask & (~collision_mask)
                self.total_rewards += r_escape * valid_escape.float() * active_f
                
                self.active_mask &= ~valid_escape
                
                valid_toofar = too_far_mask & (~escaped_mask) & (~collision_mask)
                self.total_rewards += r_toofar * valid_toofar.float() * active_f
                
                valid_sweet = sweet_spot_mask & (~collision_mask)
                self.total_rewards += r_sweet * valid_sweet.float() * active_f

            # obs_pos = self.sim.pos.reshape(self.num_envs, -1)
            # obs_v = self.sim.v.reshape(self.num_envs, -1)
            # obs_m = self.sim.masses.squeeze(2).reshape(self.num_envs, -1)
            
            next_obs = self._get_obs()
            terminated = torch.ones(self.num_envs, device=self.device)
            
            info = {
                "avg_steps": self.steps_alive.mean().item()
            }
            
            return next_obs, self.total_rewards, terminated, info
            
    def reset(self):
        # Re-initialize simulation with random states
        init_pos = torch.randn(self.num_envs, 3, 3).to(self.device)*5.0
        init_v = torch.randn(self.num_envs, 3, 3).to(self.device)
        self.sim.reset(new_pos=init_pos, new_v=init_v)
        
        # obs_pos = self.sim.pos.reshape(self.num_envs, -1)
        # obs_v = self.sim.v.reshape(self.num_envs, -1)
        # obs_m = self.sim.masses.squeeze(2).reshape(self.num_envs, -1)
        
        # observation = torch.cat([obs_pos, obs_v, obs_m], dim=1)
        return self._get_obs()