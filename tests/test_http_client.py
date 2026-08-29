import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scrapers.http_client import ScraperHTTPClient


class TestHTTPClient:
    @pytest.mark.asyncio
    async def test_get_success(self):
        client = ScraperHTTPClient(rate_limit_per_second=1000)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jobs": []}
        mock_response.headers = {}
        
        with patch.object(client, '_get_client', return_value=MagicMock(get=AsyncMock(return_value=mock_response))):
            response = await client.get("https://example.com/api")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_retry_on_500(self):
        client = ScraperHTTPClient(max_retries=2, base_delay=0.01, rate_limit_per_second=1000)
        
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.headers = {}
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"jobs": []}
        mock_response_200.headers = {}
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=[mock_response_500, mock_response_200])
        mock_client.is_closed = False
        
        with patch.object(client, '_get_client', return_value=mock_client):
            response = await client.get("https://example.com/api")
            assert response.status_code == 200
            assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_429_with_retry_after(self):
        client = ScraperHTTPClient(max_retries=2, base_delay=0.01, rate_limit_per_second=1000)
        
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "0.01"}
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"jobs": []}
        mock_response_200.headers = {}
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=[mock_response_429, mock_response_200])
        mock_client.is_closed = False
        
        with patch.object(client, '_get_client', return_value=mock_client):
            response = await client.get("https://example.com/api")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        client = ScraperHTTPClient(rate_limit_per_second=10, max_retries=0)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jobs": []}
        mock_response.headers = {}
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        
        import time
        start = time.time()
        with patch.object(client, '_get_client', return_value=mock_client):
            await client.get("https://example.com/api")
            await client.get("https://example.com/api")
        elapsed = time.time() - start
        # Should take at least 0.1 seconds for 2 requests at 10/sec
        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_close(self):
        client = ScraperHTTPClient()
        mock_client = MagicMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        
        # Set the internal client directly
        client._client = mock_client
        await client.close()
        mock_client.aclose.assert_called_once()


class TestScraperErrorHandling:
    @pytest.mark.asyncio
    async def test_remoteok_fetch_handles_error(self):
        from app.scrapers.remoteok import fetch_jobs
        
        with patch("app.scrapers.remoteok.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_get_client.return_value = mock_client
            
            jobs = await fetch_jobs()
            assert jobs == []

    @pytest.mark.asyncio
    async def test_greenhouse_fetch_handles_error(self):
        from app.scrapers.greenhouse import fetch_jobs
        
        with patch("app.scrapers.greenhouse.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_get_client.return_value = mock_client
            
            jobs = await fetch_jobs("test-slug")
            assert jobs == []

    @pytest.mark.asyncio
    async def test_lever_fetch_handles_error(self):
        from app.scrapers.lever import fetch_jobs
        
        with patch("app.scrapers.lever.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_get_client.return_value = mock_client
            
            jobs = await fetch_jobs("test-slug")
            assert jobs == []

    @pytest.mark.asyncio
    async def test_ashby_fetch_handles_error(self):
        from app.scrapers.ashby import fetch_jobs
        
        with patch("app.scrapers.ashby.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_get_client.return_value = mock_client
            
            jobs = await fetch_jobs("test-slug")
            assert jobs == []