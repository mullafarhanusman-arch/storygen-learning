import os
import json
import base64
import tempfile
from typing import Dict, Any, List
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.adk.tools import BaseTool, ToolContext
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()


class ImagenTool:
    """
    Custom ADK tool for generating images using Google Vertex AI Imagen.
    Automatically stores images in GCS bucket to avoid MCP token payload issues.
    """
    
    async def run(self, prompt: str, **kwargs) -> str:
        """Generate an image using Vertex AI Imagen and store in GCS bucket."""
        try:
            prompt = kwargs.get("prompt", "")
            negative_prompt = kwargs.get(
                "negative_prompt",
                "photorealistic, realistic, blurry, low quality, watermark, text overlay"
            )
            aspect_ratio = kwargs.get("aspect_ratio", "16:9")
            number_of_images = kwargs.get("number_of_images", 1)
            
            if not prompt.strip():
                return json.dumps({
                    "error": "Prompt is required for image generation"
                })
            
            # Apply strict cartoon style prefix
            style_prefix = (
                "Children's book illustration in cartoon style with bright vibrant colors, simple shapes, and friendly characters. "
            )
            full_prompt = f"{style_prefix} {prompt}".strip()
            
            print(f"🎨 Generating image with prompt: {full_prompt}")
            
            # Generate image using Vertex AI Imagen
            response = self._model.generate_images(
                prompt=full_prompt,
                number_of_images=number_of_images,
                negative_prompt=negative_prompt,
                aspect_ratio=aspect_ratio
            )
            
            # Access the images property of the response
            images = response.images if hasattr(response, 'images') else []
            
            image_results = []
            
            for i, image in enumerate(images):
                try:
                    # Save to temporary file first
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                        image.save(location=temp_file.name)
                        
                        # If bucket is configured, upload to GCS
                        if self._storage_client and self._bucket_name:
                            try:
                                gcs_url = self._upload_to_bucket(temp_file.name, full_prompt, i)
                                image_results.append({
                                    "index": i,
                                    "gcs_url": gcs_url,
                                    "format": "png",
                                    "stored_in_bucket": True
                                })
                                print(f"✅ Image {i} uploaded to GCS: {gcs_url}")
                            except Exception as e:
                                print(f"❌ Failed to upload image {i} to bucket: {e}")
                                # Fallback to base64 if bucket upload fails
                                with open(temp_file.name, "rb") as img_file:
                                    img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                                    image_results.append({
                                        "index": i,
                                        "base64": img_base64,
                                        "format": "png",
                                        "stored_in_bucket": False,
                                        "bucket_error": str(e)
                                    })
                        else:
                            # No bucket configured, return base64
                            with open(temp_file.name, "rb") as img_file:
                                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                                image_results.append({
                                    "index": i,
                                    "base64": img_base64,
                                    "format": "png",
                                    "stored_in_bucket": False
                                })
                        
                        # Clean up temporary file
                        os.unlink(temp_file.name)
                        
                except Exception as e:
                    image_results.append({
                        "index": i,
                        "error": f"Failed to process image: {str(e)}"
                    })
            
            # Count successful bucket uploads
            bucket_uploads = sum(1 for result in image_results if result.get("stored_in_bucket", False))
            
            result = {
                "success": True,
                "images_generated": len(image_results),
                "images_in_bucket": bucket_uploads,
                "bucket_name": self._bucket_name if self._storage_client else None,
                "token_safe": bucket_uploads > 0,  # Indicate if we avoided token issues
                "images": image_results
            }
            
            return json.dumps(result)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Image generation failed: {str(e)}"
            })
    

    def _upload_to_bucket(self, local_path: str, prompt: str, index: int) -> str:
        """Upload image to GCS bucket and return public URL."""
        if not self._storage_client or not self._bucket_name:
            raise Exception("GCS client or bucket not configured")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        # Sanitize prompt for filename
        safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_prompt = safe_prompt.replace(' ', '_')
        
        blob_name = f"generated_images/{timestamp}_{safe_prompt}_{index}_{unique_id}.png"
        
        # Upload to bucket
        bucket = self._storage_client.bucket(self._bucket_name)
        blob = bucket.blob(blob_name)
        
        with open(local_path, 'rb') as image_file:
            blob.upload_from_file(image_file, content_type='image/png')

        # Make the blob publicly readable
        blob.make_public()
        
        # Don't use make_public() with uniform bucket-level access
        # Instead, assume the bucket is already public or use the public URL format
        # Return public HTTPS URL for browser display
        return blob.public_url