from facenet_pytorch import InceptionResnetV1, MTCNN
import torch

device = 'cuda' if torch.cuda.is_available() else 'cpu'

mtcnn = MTCNN(
    image_size=160,
    margin=0,
    device=device
)

model = InceptionResnetV1(
    pretrained='vggface2'
).eval().to(device)
