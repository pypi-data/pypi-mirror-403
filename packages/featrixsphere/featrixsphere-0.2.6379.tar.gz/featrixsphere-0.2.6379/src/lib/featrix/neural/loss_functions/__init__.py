# Loss function versions
#
# Each file is a self-contained set of loss functions for a specific date/version.
# All files implement the same interface (LossComponent base class, LossFramework).
#
# To use a specific version:
#   from featrix.neural.loss_functions import loss_functions_21Jan2026 as losses
#   framework = losses.create_default_framework()
#
# Available versions:
#   - loss_functions_01Jan2026: Pure InfoNCE (joint + marginal + spread), adaptive temperature
#   - loss_functions_21Jan2026: Cosine → InfoNCE curriculum, UniformityLoss on masked embeddings
