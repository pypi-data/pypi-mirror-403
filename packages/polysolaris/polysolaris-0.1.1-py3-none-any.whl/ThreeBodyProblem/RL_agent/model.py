import torch
import torch.nn as nn
import torch.nn.functional as f
class ResBlock(nn.Module):
    def __init__(self, hidden_size, ):
        super(ResBlock, self).__init__()
        self.fc1 = nn.Linear(hidden_size, hidden_size)
        self.ln1 = nn.LayerNorm(hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.ln2 = nn.LayerNorm(hidden_size)
    def forward(self, x):
        identity = x
        x = self.fc1(x)
        x = self.ln1(x)
        x = self.fc2(x)
        x = self.ln2(x)
        x += identity
        return x

class AttentionBlock(nn.Module):
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        self.layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim*4, 
            batch_first=True,
            norm_first=True
        )
    def forward(self, x):
        return self.layer(x)
class Actor_Critic(nn.Module):
    def __init__(
        self,
        num_input,
        num_output
    ):
        super(Actor_Critic, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=num_input//3, out_channels=32, kernel_size=1)
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=1)
        self.conv3 = nn.Conv1d(in_channels=64, out_channels=128, kernel_size=1)
        
        self.attn = AttentionBlock(embed_dim=128, num_heads=4)
        self.flatten_dim = 3*128

        self.fc1 = nn.Linear(self.flatten_dim, 512)
        self.ln1 = nn.LayerNorm(512)
        self.res_block1 = ResBlock(512)
        self.res_block2 = ResBlock(512)
        # self.critic1 = ResBlock(512)
        self.critic1 = ResBlock(512)
        self.critic2 = ResBlock(512)
        self.critic3 = nn.Linear(512, 256)
        self.critic4 = ResBlock(256)
        self.critic5 = nn.Linear(256, 1)

        self.actor1 = ResBlock(512)
        self.actor2 = ResBlock(512)
        self.actor3 = nn.Linear(512, num_output)
        self.log_std = nn.Parameter(torch.zeros(num_output))

    def forward(self, x):
        #data prep
        batch_size = x.shape[0]
        rel_pos = x[:, 0:9].view(batch_size, 3, 3) / 50.0
        vel = x[:, 9:18].view(batch_size, 3, 3) / 5.0
        mass = x[:, 18:21].view(batch_size, 3, 1)
        # accel     = x[:, 21:30].view(batch_size, 3, 3)
        # potential = x[:, 30:33].view(batch_size, 3, 1)
        # angles    = x[:, 33:36].view(batch_size, 3, 1)
        bodies = torch.cat([rel_pos, vel, mass], dim=2)
        cnn_input = bodies.permute(0, 2, 1)

        #cnn
        x_cnn = self.conv1(cnn_input)
        x_cnn = f.relu(x_cnn)
        x_cnn = self.conv2(x_cnn)
        x_cnn = f.relu(x_cnn)
        x_cnn = self.conv3(x_cnn)
        x_cnn = f.relu(x_cnn)
        
        attn_input = x_cnn.permute(0, 2, 1)
        x_attn = self.attn(attn_input)
        x = x_attn.reshape(batch_size, -1)

        #res&linear
        x = self.fc1(x)
        x = self.ln1(x)
        x = f.relu(x)
        x = self.res_block1(x)
        x = f.relu(x)
        x = self.res_block2(x)
        x = f.relu(x)

        #actor
        a = self.actor1(x)
        a = f.relu(a)
        a = self.actor2(a)
        a = f.relu(a)
        action_mean = self.actor3(a)

        #critic
        value = self.critic1(x)
        value = f.relu(value)
        value = self.critic2(value)
        value = f.relu(value)
        value = self.critic3(value)
        value = f.relu(value)
        value = self.critic4(value)
        value = f.relu(value)
        value = self.critic5(value)
        # value = self.critic3(value)
        return action_mean, value, self.log_std