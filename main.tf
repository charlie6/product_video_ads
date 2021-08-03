variable "client_id" {
  type = string
}

variable "client_secret" {
  type = string
}

variable "access_token" {
  type = string
}

variable "refresh_token" {
  type = string
}

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

resource "google_project_service" "enable_google_drive_api" {
  project = data.google_client_config.current.project
  service = "drive.googleapis.com"
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
        env {
          name = "GCP_PROJECT"
          value = data.google_client_config.current.project
        }
        env {
          name = "CLIENT_ID"
          value = var.client_id
        }
        env {
          name = "CLIENT_SECRET"
          value = var.client_secret
        }
        env {
          name = "ACCESS_TOKEN"
          value = var.access_token
        }
        env {
          name = "REFRESH_TOKEN"
          value = var.refresh_token
        }
        ports {
            container_port = 5055
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

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.product_video_ads_service.location
  project     = google_cloud_run_service.product_video_ads_service.project
  service     = google_cloud_run_service.product_video_ads_service.name

  policy_data = data.google_iam_policy.noauth.policy_data
}

output "url" {
  value = "${google_cloud_run_service.product_video_ads_service.status[0].url}"
}