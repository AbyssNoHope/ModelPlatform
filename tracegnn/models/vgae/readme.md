### Train

python3 -m tracegnn.models.vgae.train

### Test

python3 -m tracegnn.models.vgae.test evaluate-nll -D dataset_name -M model_path --device cuda/cpu --flag
