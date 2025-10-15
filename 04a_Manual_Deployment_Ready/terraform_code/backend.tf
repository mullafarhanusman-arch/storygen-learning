terraform {
  backend "gcs" {
    bucket  = "storygen-tf-state-bucket" # This will be replaced by the script
    prefix  = "terraform/state"
  }
}
