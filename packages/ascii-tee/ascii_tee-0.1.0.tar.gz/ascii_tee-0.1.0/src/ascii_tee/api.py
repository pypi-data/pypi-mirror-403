"""HTTP client for ASCII Tee backend API."""

import base64
from pathlib import Path

import httpx
from ascii_tee.models import Design, Order

# Default to local dev; override with env var in production
DEFAULT_API_URL = "http://localhost:8787"


class APIError(Exception):
    """Raised when the API returns an error."""

    pass


class APIClient:
    """Client for the ASCII Tee backend API."""

    def __init__(self, base_url: str = DEFAULT_API_URL, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate_ascii(self, prompt: str, remove_background: bool = False) -> Design:
        """Generate ASCII art from a prompt.

        Args:
            prompt: Description of desired ASCII art
            remove_background: If True, trim background and return just the art

        Returns:
            Design object with generated ASCII art

        Raises:
            APIError: If the API request fails
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/generate",
                json={"prompt": prompt, "remove_background": remove_background},
            )

        if response.status_code != 200:
            error = response.json().get("error", "Unknown error")
            raise APIError(f"Failed to generate ASCII art: {error}")

        data = response.json()
        return Design(
            prompt=data["prompt"],
            ascii_art=data["ascii_art"],
        )

    def upload_preview(self, design_id: str, image_path: Path) -> str:
        """Upload a preview image to get a public URL.

        Args:
            design_id: Unique design identifier
            image_path: Path to the PNG preview image

        Returns:
            Public URL for the uploaded image

        Raises:
            APIError: If the API request fails
        """
        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/upload",
                json={
                    "design_id": design_id,
                    "image_data": image_data,
                },
            )

        if response.status_code != 200:
            error = response.json().get("error", "Unknown error")
            raise APIError(f"Failed to upload preview: {error}")

        data = response.json()
        return data["image_url"]

    def upload_print_file(self, design_id: str, color: str, image_path: Path) -> str:
        """Upload a print file to get a public URL for Printful.

        Args:
            design_id: Unique design identifier
            color: Shirt color (used in filename)
            image_path: Path to the PNG print file

        Returns:
            Public URL for the uploaded print file

        Raises:
            APIError: If the API request fails
        """
        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/upload",
                json={
                    "design_id": f"print_{design_id}_{color}",
                    "image_data": image_data,
                },
            )

        if response.status_code != 200:
            error = response.json().get("error", "Unknown error")
            raise APIError(f"Failed to upload print file: {error}")

        data = response.json()
        return data["image_url"]

    def create_checkout(self, order: Order, image_url: str | None = None, print_file_url: str | None = None) -> str:
        """Create a Stripe checkout session.

        Args:
            order: Order with design, color, size, quantity
            image_url: Optional URL to preview image for checkout page

        Returns:
            Checkout URL to open in browser

        Raises:
            APIError: If the API request fails
        """
        payload = {
            "design_id": order.design.id,
            "ascii_art": order.design.ascii_art,
            "prompt": order.design.prompt,
            "color": order.color,
            "size": order.size,
            "quantity": order.quantity,
        }

        if image_url:
            payload["image_url"] = image_url

        if print_file_url:
            payload["print_file_url"] = print_file_url

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/checkout",
                json=payload,
            )

        if response.status_code != 200:
            error = response.json().get("error", "Unknown error")
            raise APIError(f"Failed to create checkout: {error}")

        data = response.json()
        return data["checkout_url"]
