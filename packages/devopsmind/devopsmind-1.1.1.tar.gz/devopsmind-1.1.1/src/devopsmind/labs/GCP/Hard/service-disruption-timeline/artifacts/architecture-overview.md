# GCP Architecture Overview

- Public web application
- Global HTTP(S) Load Balancer
- Compute Engine instances in two zones (us-central1-a, us-central1-b)
- Instances belong to a single backend service
- Static assets served from Cloud Storage
