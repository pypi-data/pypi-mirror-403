import argparse
import csv
from pathlib import Path
from typing import Any, Iterable, Optional

import joblib
from pydantic import BaseModel, Field, ValidationError, field_validator

from spam_classifier.config.core import read_package_version
from spam_classifier.config.paths import ROOT, TRAINED_MODEL_DIR


class PredictionInput(BaseModel):
    message: str = Field(min_length=1)

    @field_validator("message")
    @classmethod
    def non_empty_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must be a non-empty string")
        return value


class PredictionOutput(BaseModel):
    label: str
    score: Optional[float] = None


def load_model(model_path: Optional[Path] = None) -> Any:
    if model_path is None:
        version = read_package_version()
        model_path = TRAINED_MODEL_DIR / f"spam_classifier_v{version}.pkl"
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Trained model not found at {model_path!s}. Train the model first or pass --model-path."
        )
    return joblib.load(model_path)


def predict_message(message: str, model: Any) -> PredictionOutput:
    validated = PredictionInput(message=message)
    pred = model.predict([validated.message])[0]
    label = "spam" if pred == 1 else "ham"

    score = None
    if hasattr(model, "predict_proba"):
        score = float(model.predict_proba([validated.message])[0][1])

    return PredictionOutput(label=label, score=score)


def predict_messages(messages: Iterable[str], model: Any) -> list[PredictionOutput]:
    outputs: list[PredictionOutput] = []
    for message in messages:
        outputs.append(predict_message(message, model))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Spam classifier inference")
    parser.add_argument("input", help="Message text or path to a file with messages")
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path for batch predictions (CSV). Defaults to project root.",
    )
    parser.add_argument(
        "--model-path",
        help="Path to a trained model .pkl file. Defaults to versioned model in package.",
    )
    parser.add_argument(
        "--no-message",
        action="store_true",
        help="Do not include the message text in the output CSV.",
    )
    args = parser.parse_args()

    model_path = Path(args.model_path) if args.model_path else None
    model = load_model(model_path)
    arg = args.input
    path = Path(arg)
    try:
        if path.is_file():
            lines = path.read_text(encoding="utf-8").splitlines()
            records = [(idx + 1, line) for idx, line in enumerate(lines) if line.strip()]
            outputs = predict_messages((text for _, text in records), model)

            if args.output:
                output_path = Path(args.output)
            else:
                output_name = f"{path.stem}.pred.csv"
                output_path = ROOT / output_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if args.no_message:
                    writer.writerow(["line", "label", "score"])
                else:
                    writer.writerow(["line", "message", "label", "score"])
                for (line_no, message), output in zip(records, outputs):
                    score = f"{output.score:.6f}" if output.score is not None else ""
                    if args.no_message:
                        writer.writerow([line_no, output.label, score])
                    else:
                        writer.writerow([line_no, message, output.label, score])

            print(f"Saved predictions to {output_path}")
            return 0
        output = predict_message(arg, model)
    except (ValidationError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    if output.score is not None:
        print(f"label={output.label} score={output.score:.4f}")
    else:
        print(f"label={output.label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
