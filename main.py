import os
from embeddings.fasttext_model import FastTextTrainer
from gensim.models import FastText


def main():
    output_model_file = "rest_model"

    if os.path.exists(output_model_file):
        print(f"Loading existing model from '{output_model_file}'.")
        model = FastText.load(output_model_file)
    else:
        print(f"Training new model, as '{output_model_file}' not found.")
        ft_trainer = FastTextTrainer(specs_dir="./APIs-guru/specifications", output_model_file=output_model_file)
        model = ft_trainer.train_model()


if __name__ == "__main__":
    main()
