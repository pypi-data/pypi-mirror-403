import gymnasium_sudoku,torch,sys
import gymnasium as gym
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
import numpy as np
import time
from tqdm import tqdm


def process_obs(x): 
    m = (x == 0).unsqueeze(1).float()
    x = F.one_hot(x,num_classes=10).permute(0,-1,1,2).float() 
    return torch.cat([x,m],dim=1) 

class p_net(nn.Module):
    def __init__(self):
        super().__init__()
        self.c1 = nn.LazyConv2d(64,1,1)
        self.c2 = nn.LazyConv2d(128,3,1,padding=1)
        self.c3 = nn.LazyConv2d(128,3,1,padding=1)
        self.emb = nn.Parameter(torch.randn(1,81,128) * 0.02)
        self.attn = nn.MultiheadAttention(128,4,batch_first=True)
        self.norm = nn.LayerNorm(128)
        self.l1 = nn.LazyLinear(128)
        self.l2 = nn.LazyLinear(128)
        self.pos = nn.LazyLinear(1)
        self.num = nn.LazyLinear(10)
        self.v_aux = nn.LazyLinear(1)
        self.register_buffer("attn_mask",self.attn_masks())
    
    def forward(self,s):
        x = self.c1(s)
        x = F.silu(self.c2(x))  
        x = F.silu(self.c3(x))
        x = x.flatten(2).transpose(-1,1) 
        x = x + self.emb
        x,asc= self.attn(x,x,x,attn_mask=self.attn_mask,average_attn_weights=True)
        x = self.norm(x)
        x = F.silu(self.l1(x))
        x = F.silu(self.l2(x))
        pos = self.pos(x).squeeze(-1)
        pos = self.pos_mask(s,pos)
        pos = F.softmax(pos,-1)
        pos = Categorical(probs=pos).sample()
        num_logits = self.num(x)  
        idx = torch.arange(x.size(0))
        o = num_logits[idx,pos]
        o = self.action_mask(o)
        o = F.softmax(o,-1)
        num = Categorical(probs=o).sample()
        return pos,num,asc

    def pos_mask(self,s,x): 
        s = s.argmax(1)
        mask = (s!=0).flatten(1)
        value = -1e9
        return torch.masked_fill(x,mask,value)

    def action_mask(self,x): 
        mask = torch.zeros_like(x,dtype=torch.bool)   
        mask[:,0] = True
        value = -float("inf")
        return torch.masked_fill(x,mask,value)
    
    def attn_masks(self,N=81):
        indices = torch.arange(N)  

        rows = indices // 9 
        cols = indices % 9      
        boxes = (rows // 3) * 3 + (cols // 3)  # shape [81]

        row_mask = (rows.unsqueeze(0)==rows.unsqueeze(1)).float()
        col_mask = (cols.unsqueeze(0)==cols.unsqueeze(1)).float()
        box_mask = (boxes.unsqueeze(0)==boxes.unsqueeze(1)).float()
        global_mask = torch.ones(N, N)
        return torch.stack([row_mask,col_mask,box_mask,global_mask],dim=0)

env = gym.make(
        "sudoku-v0",
        mode = "biased",
        render_mode="human",
        horizon=800,
        eval_mode=True
    )

env.reset()
total_steps = int(6e3*5) 
steps = 0

policy = p_net()
policy(process_obs(torch.randint(0,9,(1,9,9))))
#t_policy = torch.load("./model_test",map_location="cpu")["policy state"]
#policy.load_state_dict(t_policy,strict=False)

obs = env.reset()[0]
steps = r = 0

for n in range(total_steps):
    #pos,num,attn = policy(process_obs(torch.tensor(obs,dtype=torch.int64).unsqueeze(0)))
    #xpos = pos // 9 ; ypos = pos % 9
    #action = np.stack((xpos,ypos,num),axis=-1).reshape(3)
    obs,reward,done,trunc,_ = env.step(env.action_space.sample())
    steps+=1 ; r+=reward
    print(reward)
    env.render()
    if done:
        print(f"\n{obs} | steps : {steps} | reward {r:.2f}")
        time.sleep(5)
        steps = r = 0
        obs = env.reset()[0]
