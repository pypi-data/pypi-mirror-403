use flate2::read::ZlibDecoder;
use flate2::write::ZlibEncoder;
use flate2::Compression;
use image::codecs::jpeg::JpegEncoder;
use image::{DynamicImage, ImageReader};
use lopdf::{Document, Object, ObjectId, Stream};
use std::io::{Cursor, Read, Write};

#[derive(Debug, Clone, Copy)]
pub enum CompressionLevel {
    Extreme,     // 30% quality
    Recommended, // 60% quality
    Low,         // 85% quality
}

impl CompressionLevel {
    pub fn quality(&self) -> u8 {
        match self {
            CompressionLevel::Extreme => 30,
            CompressionLevel::Recommended => 60,
            CompressionLevel::Low => 85,
        }
    }

    pub fn scale_factor(&self) -> f32 {
        match self {
            CompressionLevel::Extreme => 0.5,
            CompressionLevel::Recommended => 0.75,
            CompressionLevel::Low => 1.0,
        }
    }
}

pub struct PdfCompressor {
    level: CompressionLevel,
}

impl PdfCompressor {
    pub fn new(level: CompressionLevel) -> Self {
        Self { level }
    }

    pub fn compress(&self, input: &[u8]) -> Result<Vec<u8>, String> {
        let mut doc =
            Document::load_mem(input).map_err(|e| format!("Failed to load PDF: {}", e))?;

        // Remove metadata
        self.remove_metadata(&mut doc);

        // Compress images
        self.compress_images(&mut doc)?;

        // Compress streams
        self.compress_streams(&mut doc);

        // Save to bytes
        let mut output = Vec::new();
        doc.save_to(&mut output)
            .map_err(|e| format!("Failed to save PDF: {}", e))?;

        Ok(output)
    }

    fn remove_metadata(&self, doc: &mut Document) {
        // Remove document info dictionary
        if let Ok(info_id) = doc.trailer.get(b"Info") {
            if let Ok(reference) = info_id.as_reference() {
                doc.delete_object(reference);
            }
        }
        doc.trailer.remove(b"Info");
    }

    fn compress_images(&self, doc: &mut Document) -> Result<(), String> {
        let object_ids: Vec<ObjectId> = doc.objects.keys().cloned().collect();

        for id in object_ids {
            if let Ok(object) = doc.get_object(id) {
                if let Object::Stream(stream) = object.clone() {
                    if self.is_image_stream(&stream) {
                        if let Some(compressed) = self.compress_image_stream(&stream) {
                            if let Ok(obj) = doc.get_object_mut(id) {
                                *obj = Object::Stream(compressed);
                            }
                        }
                    }
                }
            }
        }

        Ok(())
    }

    fn is_image_stream(&self, stream: &Stream) -> bool {
        if let Ok(subtype) = stream.dict.get(b"Subtype") {
            if let Ok(name) = subtype.as_name() {
                return name == b"Image";
            }
        }
        false
    }

    fn compress_image_stream(&self, stream: &Stream) -> Option<Stream> {
        // Get image properties
        let width = stream.dict.get(b"Width").ok()?.as_i64().ok()? as u32;
        let height = stream.dict.get(b"Height").ok()?.as_i64().ok()? as u32;
        let bits_per_component = stream
            .dict
            .get(b"BitsPerComponent")
            .ok()
            .and_then(|o| o.as_i64().ok())
            .unwrap_or(8) as u8;

        // Get color space
        let color_space = stream
            .dict
            .get(b"ColorSpace")
            .ok()
            .and_then(|o| o.as_name().ok())
            .map(|n| String::from_utf8_lossy(n).to_string())
            .unwrap_or_else(|| "DeviceRGB".to_string());

        // Decode stream content
        let content = self.decode_stream_content(stream)?;

        // Try to decode as image
        let image =
            self.decode_image_data(&content, width, height, bits_per_component, &color_space)?;

        // Compress as JPEG
        let compressed = self.encode_as_jpeg(&image)?;

        // Create new stream
        let mut new_dict = stream.dict.clone();
        new_dict.set("Filter", Object::Name(b"DCTDecode".to_vec()));
        new_dict.remove(b"DecodeParms");
        new_dict.set("ColorSpace", Object::Name(b"DeviceRGB".to_vec()));
        new_dict.set("BitsPerComponent", Object::Integer(8));

        // Update dimensions if scaled
        let scale = self.level.scale_factor();
        if scale < 1.0 {
            let new_width = (width as f32 * scale) as i64;
            let new_height = (height as f32 * scale) as i64;
            new_dict.set("Width", Object::Integer(new_width));
            new_dict.set("Height", Object::Integer(new_height));
        }

        Some(Stream::new(new_dict, compressed))
    }

    fn decode_stream_content(&self, stream: &Stream) -> Option<Vec<u8>> {
        let filter = stream.dict.get(b"Filter").ok();

        match filter {
            Some(Object::Name(name)) => {
                let filter_name = String::from_utf8_lossy(name);
                match filter_name.as_ref() {
                    "FlateDecode" => self.decode_flate(&stream.content),
                    "DCTDecode" => Some(stream.content.clone()), // Already JPEG
                    _ => None,
                }
            }
            Some(Object::Array(filters)) => {
                // Handle filter chain
                let mut data = stream.content.clone();
                for f in filters.iter().rev() {
                    if let Object::Name(name) = f {
                        let filter_name = String::from_utf8_lossy(name);
                        data = match filter_name.as_ref() {
                            "FlateDecode" => self.decode_flate(&data)?,
                            "DCTDecode" => data,
                            _ => return None,
                        };
                    }
                }
                Some(data)
            }
            None => Some(stream.content.clone()),
            _ => None,
        }
    }

    fn decode_flate(&self, data: &[u8]) -> Option<Vec<u8>> {
        let mut decoder = ZlibDecoder::new(data);
        let mut decoded = Vec::new();
        decoder.read_to_end(&mut decoded).ok()?;
        Some(decoded)
    }

    fn decode_image_data(
        &self,
        data: &[u8],
        width: u32,
        height: u32,
        bits: u8,
        color_space: &str,
    ) -> Option<DynamicImage> {
        // Try to decode as common image format first
        if let Ok(reader) = ImageReader::new(Cursor::new(data)).with_guessed_format() {
            if let Ok(img) = reader.decode() {
                return Some(img);
            }
        }

        // Try to interpret as raw image data
        if bits == 8 {
            let channels = match color_space {
                "DeviceRGB" => 3,
                "DeviceGray" => 1,
                "DeviceCMYK" => 4,
                _ => return None,
            };

            let expected_len = (width * height * channels) as usize;
            if data.len() >= expected_len {
                match channels {
                    1 => {
                        image::GrayImage::from_raw(width, height, data[..expected_len].to_vec())
                            .map(DynamicImage::ImageLuma8)
                    }
                    3 => {
                        image::RgbImage::from_raw(width, height, data[..expected_len].to_vec())
                            .map(DynamicImage::ImageRgb8)
                    }
                    4 => {
                        // Convert CMYK to RGB
                        let rgb_data: Vec<u8> = data[..expected_len]
                            .chunks(4)
                            .flat_map(|cmyk| {
                                let c = cmyk[0] as f32 / 255.0;
                                let m = cmyk[1] as f32 / 255.0;
                                let y = cmyk[2] as f32 / 255.0;
                                let k = cmyk[3] as f32 / 255.0;
                                let r = (255.0 * (1.0 - c) * (1.0 - k)) as u8;
                                let g = (255.0 * (1.0 - m) * (1.0 - k)) as u8;
                                let b = (255.0 * (1.0 - y) * (1.0 - k)) as u8;
                                vec![r, g, b]
                            })
                            .collect();
                        image::RgbImage::from_raw(width, height, rgb_data)
                            .map(DynamicImage::ImageRgb8)
                    }
                    _ => None,
                }
            } else {
                None
            }
        } else {
            None
        }
    }

    fn encode_as_jpeg(&self, image: &DynamicImage) -> Option<Vec<u8>> {
        let scale = self.level.scale_factor();
        let image = if scale < 1.0 {
            let new_width = (image.width() as f32 * scale) as u32;
            let new_height = (image.height() as f32 * scale) as u32;
            image.resize(
                new_width,
                new_height,
                image::imageops::FilterType::Lanczos3,
            )
        } else {
            image.clone()
        };

        let rgb = image.to_rgb8();
        let mut output = Vec::new();
        let mut encoder = JpegEncoder::new_with_quality(&mut output, self.level.quality());
        encoder
            .encode(
                &rgb,
                rgb.width(),
                rgb.height(),
                image::ExtendedColorType::Rgb8,
            )
            .ok()?;
        Some(output)
    }

    fn compress_streams(&self, doc: &mut Document) {
        let object_ids: Vec<ObjectId> = doc.objects.keys().cloned().collect();

        for id in object_ids {
            if let Ok(object) = doc.get_object_mut(id) {
                if let Object::Stream(ref mut stream) = object {
                    // Skip image streams (already processed)
                    if self.is_image_stream(stream) {
                        continue;
                    }

                    // Check if already compressed
                    if let Ok(filter) = stream.dict.get(b"Filter") {
                        if let Ok(name) = filter.as_name() {
                            if name == b"FlateDecode" {
                                continue; // Already compressed
                            }
                        }
                    }

                    // Compress with flate
                    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::best());
                    if encoder.write_all(&stream.content).is_ok() {
                        if let Ok(compressed) = encoder.finish() {
                            if compressed.len() < stream.content.len() {
                                stream
                                    .dict
                                    .set("Filter", Object::Name(b"FlateDecode".to_vec()));
                                stream.content = compressed;
                            }
                        }
                    }
                }
            }
        }
    }
}
