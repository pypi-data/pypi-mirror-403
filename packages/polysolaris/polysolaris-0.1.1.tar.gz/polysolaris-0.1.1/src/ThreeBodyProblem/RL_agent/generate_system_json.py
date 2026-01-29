from ThreeBodyProblem.RL_agent.model import Actor_Critic
import os
import json
import torch
import numpy as np
from pathlib import Path

def create_body(name, body_id, mass, position, velocity, colour, simulation=1, create_stable_orbit=0, eccentricity=0, central_body_id=0):
    if central_body_id == body_id:
        central_body_id = None
    return {
        "name": name,
        "id": body_id,
        "mass": mass,
        "initial_position": position,
        "initial_velocity": velocity,
        "create_stable_orbit": create_stable_orbit,
        "eccentricity": eccentricity,
        "id_of_central_body": central_body_id,
        "colour": colour,
        "simulation": simulation,
    }

def main():
    masses_val = [1.0, 1.0, 1.0]
    base_dir = Path(__file__).resolve().parents[2]

    model_path = Path("best_agent.pth")
    if not model_path.exists():
        model_path = Path("../best_agent.pth") 
    
    if not model_path.exists():
        print("Error: best_agent.pth not found in current or parent directory.")
        return

    data_dir = base_dir / "system_simulation" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "predicted_system.json"

    device = "cuda" if torch.cuda.is_available() else "cpu"

    agent = Actor_Critic(21, 9).to(device)
    agent.load_state_dict(torch.load(model_path, map_location=device))
    agent.eval()

    abs_pos = torch.randn(1, 3, 3).to(device) * 5.0
    
    init_v = torch.randn(1, 3, 3).to(device)
    
    mass_tensor = torch.tensor([masses_val], dtype=torch.float32).to(device)

    p1, p2, p3 = abs_pos[:, 0], abs_pos[:, 1], abs_pos[:, 2]
    
    rel_pos12 = p1 - p2
    rel_pos23 = p2 - p3
    rel_pos31 = p3 - p1
    
    eps = 1e-6
    dist12 = rel_pos12.norm(dim=1, keepdim=True) + eps
    dist23 = rel_pos23.norm(dim=1, keepdim=True) + eps
    dist31 = rel_pos31.norm(dim=1, keepdim=True) + eps

    d12_cubed = dist12.pow(3)
    d23_cubed = dist23.pow(3)
    d31_cubed = dist31.pow(3)

    m1, m2, m3 = mass_tensor[:, 0], mass_tensor[:, 1], mass_tensor[:, 2]
    m1, m2, m3 = m1.view(-1, 1), m2.view(-1, 1), m3.view(-1, 1)

    a1 = (-m2 * rel_pos12 / d12_cubed) + (m3 * rel_pos31 / d31_cubed)
    a2 = (-m3 * rel_pos23 / d23_cubed) + (m1 * rel_pos12 / d12_cubed)
    a3 = (-m1 * rel_pos31 / d31_cubed) + (m2 * rel_pos23 / d23_cubed)

    u1 = -(m2 / dist12) - (m3 / dist31)
    u2 = -(m1 / dist12) - (m3 / dist23)
    u3 = -(m1 / dist31) - (m2 / dist23)

    u12 = rel_pos12 / dist12
    u23 = rel_pos23 / dist23
    u31 = rel_pos31 / dist31
    
    cos_1 = (u12 * (-u31)).sum(dim=1, keepdim=True)
    cos_2 = (u23 * (-u12)).sum(dim=1, keepdim=True)
    cos_3 = (u31 * (-u23)).sum(dim=1, keepdim=True)

    flat_rel_pos = torch.cat([rel_pos12, rel_pos23, rel_pos31], dim=1)
    flat_v = init_v.reshape(1, -1)
    flat_m = mass_tensor.reshape(1, -1)
    flat_accel = torch.tanh(torch.cat([a1, a2, a3], dim=1))
    flat_potential = torch.tanh(torch.cat([u1, u2, u3], dim=1))
    flat_angles = torch.cat([cos_1, cos_2, cos_3], dim=1)

    state_vector = torch.cat([
        flat_rel_pos,   # 9
        flat_v,         # 9
        flat_m,         # 3
        flat_accel,     # 9 
        flat_potential, # 3
        flat_angles     # 3
        ], dim=1)

    with torch.no_grad():
        action_mean, _, _ = agent(state_vector)
        predicted_velocities = action_mean.cpu().numpy()[0].reshape(3, 3)

    positions_np = abs_pos.cpu().numpy()[0]

    planets = []
    colors = ["yellow", "blue", "grey"]
    names = ["Star", "Planet1", "Planet2"]

    for i in range(3):
        body = create_body(
            name=names[i],
            body_id=i,
            mass=masses_val[i],
            position=positions_np[i].tolist(),
            velocity=predicted_velocities[i].tolist(),
            colour=colors[i],
            simulation=1,
            create_stable_orbit=0,
            eccentricity=0,
            central_body_id=0 if i > 0 else None,
        )
        planets.append(body)

    system_data = {"planets": planets}

    with open(output_path, "w") as f:
        json.dump(system_data, f, indent=2)

    print(f"Generated {output_path}")
    print(f"Body 0 Pos: {positions_np[0]}")
    print(f"Body 0 Vel: {predicted_velocities[0]}")

if __name__ == "__main__":
    main()