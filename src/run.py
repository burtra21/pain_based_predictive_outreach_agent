"""Quick runner to show project layout and validate imports."""
import json, os, sys
from verticals.maritime.features.edp_features import edp_score, select_top_edp

if __name__ == "__main__":
    demo = {
        "urgency": 0.9,
        "meas": 0.8,
        "action": 0.7,
        "univer": 0.5,
        "defens": 0.6,
    }
    score = edp_score(**demo)
    print("Demo EDP score:", round(score, 3))
    print("Project base:", os.path.dirname(__file__))
