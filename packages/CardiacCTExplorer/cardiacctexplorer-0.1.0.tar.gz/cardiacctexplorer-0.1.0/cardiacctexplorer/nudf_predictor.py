"""NUDF Predictor Module"""
import torch
import numpy as np
import cardiacctexplorer.local_model as model

class NUDFPredictor:
    """NUDF Predictor Class"""
    def __init__(self, checkpoint, device = torch.device("cuda"), resolution = 16, batch_points = 1000000):
        self.model = None
        self.checkpoint = checkpoint
        self.device = device
        self.resolution = resolution
        self.batch_points = batch_points
        self.min = -0.5
        self.max = 0.5
        self.grid_points_split = None

    def setup_model(self):
        self.model = model.ShapeNet128Vox()
        self.model = self.model.to(self.device)
        self.model.eval()
        model_checkpoint = torch.load(self.checkpoint)
        self.model.load_state_dict(model_checkpoint['model_state_dict'])

        grid_points = self.create_grid_points_from_bounds(self.min, self.max, self.resolution)
        grid_points[:, 0], grid_points[:, 2] = grid_points[:, 2], grid_points[:, 0].copy()

        a = self.max + self.min
        b = self.max - self.min

        grid_coords = 2 * grid_points - a
        grid_coords = grid_coords / b

        grid_coords = torch.from_numpy(grid_coords).to(self.device, dtype=torch.float)
        grid_coords = torch.reshape(grid_coords, (1, len(grid_points), 3)).to(self.device)
        self.grid_points_split = torch.split(grid_coords, self.batch_points, dim=1)

        return True

    def create_grid_points_from_bounds(self, minimum, maximum, res):
        x = np.linspace(minimum, maximum, res)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        X = X.reshape((np.prod(X.shape),))
        Y = Y.reshape((np.prod(Y.shape),))
        Z = Z.reshape((np.prod(Z.shape),))

        points_list = np.column_stack((X, Y, Z))
        del X, Y, Z, x
        return points_list


    def predict(self, data):
        debug = False
        inputs = data['inputs']
        # Create torch tensor and send to device
        inputs = torch.from_numpy(inputs)
        inputs = inputs.to(self.device, dtype=torch.float)
        logits_list = []
        label_list = []
        idx = 0
        for points in self.grid_points_split:
            if debug:
                print(f"Computing batch {idx+1} / {len(self.grid_points_split)}")
            idx += 1
            with torch.no_grad():
                #logits = self.model(points,inputs)
                logits, out1 = self.model(points,inputs)
                #logits = out[:,0,:]
                prob_label = out1.detach().cpu()
                #print(prob_label.shape)
                pred_lab = np.argmax(prob_label.cpu(),axis=1)
                #print(pred_lab.shape)

            logits_list.append(logits.squeeze(0).detach().cpu())
            label_list.append(pred_lab.squeeze(0))

        logits = torch.cat(logits_list, dim=0)
        labels = torch.cat(label_list, dim=0)

        return logits.numpy(), labels
