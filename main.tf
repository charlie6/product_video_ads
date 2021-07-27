data "google_client_config" "current" {
}

resource "null_resource" "build_docker" {
  provisioner "local-exec" {
    command = "docker build -t gcr.io/${data.google_client_config.current.project}/product_video_ads ."
  }
}

resource "google_project_service" "enable_container_registry_api" {
  project = data.google_client_config.current.project
  service = "containerregistry.googleapis.com"
  disable_dependent_services = true
  disable_on_destroy = false
}

resource "google_project_service" "enable_cloud_run_api" {
  project = data.google_client_config.current.project
  service = "run.googleapis.com"
  disable_dependent_services = true
  disable_on_destroy = false
}

resource "null_resource" "push_docker" {
  provisioner "local-exec" {
    command = "docker push gcr.io/${data.google_client_config.current.project}/product_video_ads"
  }

  depends_on = [
    null_resource.build_docker,
    google_project_service.enable_container_registry_api
  ]
}

resource "google_cloud_run_service" "product_video_ads_service" {
  name     = "product-video-ads"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/${data.google_client_config.current.project}/product_video_ads"
        ports {
            container_port = 5000
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    null_resource.push_docker, 
    google_project_service.enable_cloud_run_api
  ]
}

output "url" {
  value = "${google_cloud_run_service.product_video_ads_service.status[0].url}"
}