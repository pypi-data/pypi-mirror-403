# Azure Highly Available Web Architecture – Requirements

The architecture must include:

- A public entry point for HTTP traffic
- A load balancing service with zone redundancy
- Compute resources deployed across multiple Availability Zones
- A highly durable storage service

Common Azure services used for this pattern include:
- Azure Application Gateway
- Azure Load Balancer
- Virtual Machines (zonal)
- Azure Blob Storage
- Virtual Network (VNet)

The design should reflect real production Azure usage.
