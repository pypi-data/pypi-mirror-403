use axum::{
    body::Body,
    extract::DefaultBodyLimit,
    http::{header, Response, StatusCode},
    response::{Html, IntoResponse},
    routing::{get, post},
    Router,
};
use axum_extra::extract::Multipart;
use tower_http::cors::{Any, CorsLayer};

use crate::pdf::{CompressionLevel, PdfCompressor};

const INDEX_HTML: &str = include_str!("../../templates/index.html");

pub fn create_router() -> Router {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        .route("/", get(index))
        .route("/api/compress", post(compress_pdf))
        .layer(DefaultBodyLimit::max(100 * 1024 * 1024)) // 100MB limit
        .layer(cors)
}

async fn index() -> Html<&'static str> {
    Html(INDEX_HTML)
}

async fn compress_pdf(mut multipart: Multipart) -> impl IntoResponse {
    let mut file_data: Option<Vec<u8>> = None;
    let mut level = CompressionLevel::Recommended;
    let mut original_filename = String::from("compressed.pdf");

    loop {
        match multipart.next_field().await {
            Ok(Some(field)) => {
                let name = field.name().unwrap_or("").to_string();
                tracing::debug!("Processing field: {}", name);

                match name.as_str() {
                    "file" => {
                        if let Some(filename) = field.file_name() {
                            original_filename = filename.to_string();
                            tracing::debug!("File name: {}", original_filename);
                        }
                        match field.bytes().await {
                            Ok(data) => {
                                tracing::debug!("File size: {} bytes", data.len());
                                file_data = Some(data.to_vec());
                            }
                            Err(e) => {
                                tracing::error!("Failed to read file data: {}", e);
                                return (
                                    StatusCode::BAD_REQUEST,
                                    format!("Failed to read file: {}", e),
                                )
                                    .into_response();
                            }
                        }
                    }
                    "level" => {
                        if let Ok(text) = field.text().await {
                            tracing::debug!("Compression level: {}", text);
                            level = match text.as_str() {
                                "extreme" => CompressionLevel::Extreme,
                                "recommended" => CompressionLevel::Recommended,
                                "low" => CompressionLevel::Low,
                                _ => CompressionLevel::Recommended,
                            };
                        }
                    }
                    _ => {
                        tracing::debug!("Ignoring unknown field: {}", name);
                    }
                }
            }
            Ok(None) => {
                tracing::debug!("No more fields");
                break;
            }
            Err(e) => {
                tracing::error!("Multipart error: {}", e);
                return (
                    StatusCode::BAD_REQUEST,
                    format!("Failed to parse multipart: {}", e),
                )
                    .into_response();
            }
        }
    }

    let file_data = match file_data {
        Some(data) if !data.is_empty() => data,
        _ => {
            tracing::error!("No file data received");
            return (StatusCode::BAD_REQUEST, "No file uploaded").into_response();
        }
    };

    let original_size = file_data.len();
    tracing::info!("Compressing {} ({} bytes)", original_filename, original_size);

    // Compress PDF
    let compressor = PdfCompressor::new(level);
    let compressed = match compressor.compress(&file_data) {
        Ok(data) => data,
        Err(e) => {
            tracing::error!("Compression failed: {}", e);
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                format!("Compression failed: {}", e),
            )
                .into_response();
        }
    };

    let compressed_size = compressed.len();
    tracing::info!(
        "Compressed {} from {} to {} bytes ({:.1}% reduction)",
        original_filename,
        original_size,
        compressed_size,
        (1.0 - compressed_size as f64 / original_size as f64) * 100.0
    );

    // Generate output filename
    let output_filename = if original_filename.ends_with(".pdf") {
        original_filename.replace(".pdf", "_compressed.pdf")
    } else {
        format!("{}_compressed.pdf", original_filename)
    };

    Response::builder()
        .status(StatusCode::OK)
        .header(header::CONTENT_TYPE, "application/pdf")
        .header(
            header::CONTENT_DISPOSITION,
            format!("attachment; filename=\"{}\"", output_filename),
        )
        .header("X-Original-Size", original_size.to_string())
        .header("X-Compressed-Size", compressed_size.to_string())
        .body(Body::from(compressed))
        .unwrap()
        .into_response()
}
