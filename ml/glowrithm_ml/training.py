"""Two-phase transfer learning shared by scripts/train.py (one run) and scripts/crossval.py (k-fold)."""
from __future__ import annotations

import time
from pathlib import Path

import keras
import numpy as np

from .data import class_weights, make_eval_dataset, make_train_dataset
from .model import build_model, count_params, set_backbones_trainable


def compile_model(model: keras.Model, learning_rate: float, label_smoothing: float) -> None:
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=label_smoothing),
        metrics=["accuracy", keras.metrics.F1Score(average="macro", name="macro_f1")],
    )


def make_callbacks(out_dir: Path, tcfg: dict, phase: str, best_so_far: float | None) -> list:
    return [
        keras.callbacks.ModelCheckpoint(str(out_dir / "best.keras"), monitor="val_macro_f1", mode="max",
                                        save_best_only=True, initial_value_threshold=best_so_far, verbose=1),
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=tcfg["early_stopping_patience"],
                                      restore_best_weights=True, verbose=1),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=tcfg["reduce_lr_factor"],
                                          patience=tcfg["reduce_lr_patience"], min_lr=1e-7, verbose=1),
        keras.callbacks.CSVLogger(str(out_dir / f"history_{phase}.csv")),
    ]


def run_training(cfg: dict, arch: str, weights, x_train, y_train, x_val, y_val, out_dir,
                 smoke_test: bool = False, verbose: int = 2) -> dict:
    """Phase 1 trains the fusion head on frozen backbones, phase 2 fine-tunes their top layers.
    Returns the best checkpoint over both phases (validation macro-F1) and run statistics."""
    tcfg, dcfg = cfg["training"], cfg["data"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n_classes = len(cfg["project"]["class_names"])
    train_ds, steps = make_train_dataset(x_train, y_train, cfg)
    val_ds = make_eval_dataset(x_val, y_val, cfg)
    weights_per_class = class_weights(y_train, n_classes) if tcfg["balance_strategy"] == "class_weight" else None
    head_epochs, ft_epochs, val_steps = tcfg["head"]["epochs"], tcfg["finetune"]["epochs"], None
    if smoke_test:
        head_epochs, ft_epochs, steps, val_steps = 1, 1, 2, 2

    model, backbones = build_model(
        arch=arch, num_classes=n_classes, img_size=dcfg["img_size"], weights=weights,
        resnet_variant=tcfg["resnet_variant"], effnet_variant=tcfg["effnet_variant"],
        dropout_1=tcfg["dropout_1"], dense_units=tcfg["dense_units"], dropout_2=tcfg["dropout_2"], l2=tcfg["l2"],
        effnet_weights_file=tcfg.get("effnet_weights_file"))

    # ---- Phase 1: train the fusion head on frozen ImageNet features ------------------------------
    set_backbones_trainable(backbones, 0.0)
    compile_model(model, tcfg["head"]["learning_rate"], tcfg["label_smoothing"])
    with open(out_dir / "model_summary.txt", "w", encoding="utf-8") as fh:
        model.summary(print_fn=lambda line, **_: fh.write(line + "\n"))
    started = time.time()
    hist_head = model.fit(train_ds, validation_data=val_ds, epochs=head_epochs, steps_per_epoch=steps,
                          validation_steps=val_steps, class_weight=weights_per_class,
                          callbacks=make_callbacks(out_dir, tcfg, "head", None), verbose=verbose)
    best_head = float(np.nanmax(hist_head.history.get("val_macro_f1", [np.nan])))

    # ---- Phase 2: fine-tune the top layers of both backbones -------------------------------------
    set_backbones_trainable(backbones, tcfg["finetune"]["unfreeze_fraction"])
    compile_model(model, tcfg["finetune"]["learning_rate"], tcfg["label_smoothing"])
    trainable, frozen = count_params(model)
    print(f"Fine-tuning: {trainable:,} trainable / {frozen:,} frozen parameters")
    start_epoch = len(hist_head.history["loss"])
    hist_ft = model.fit(train_ds, validation_data=val_ds, epochs=start_epoch + ft_epochs, initial_epoch=start_epoch,
                        steps_per_epoch=steps, validation_steps=val_steps, class_weight=weights_per_class,
                        callbacks=make_callbacks(out_dir, tcfg, "finetune", None if np.isnan(best_head) else best_head),
                        verbose=verbose)

    # ---- Best checkpoint of both phases ------------------------------------------------------------
    best = keras.saving.load_model(out_dir / "best.keras", compile=False)
    return {"model": best, "val_ds": val_ds, "backbones": [base.name for base in backbones],
            "trainable": trainable, "frozen": frozen, "finetune_start": start_epoch,
            "epochs_head": len(hist_head.history["loss"]), "epochs_finetune": len(hist_ft.history["loss"]),
            "seconds": time.time() - started}
