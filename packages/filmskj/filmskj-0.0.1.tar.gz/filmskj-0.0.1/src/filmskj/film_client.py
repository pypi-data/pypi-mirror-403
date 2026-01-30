import httpx
import backoff
from typing import Optional, List, Literal, Union, Any

from .schemas import MovieSimple, MovieDetailed, RatingSimple, TagSimple, LinkSimple, AnalyticsResponse
from .film_config import MovieConfig

import pandas as pd

class MovieClient:
    def __init__(self, config: Optional[MovieConfig] = None):
        self.config = config or MovieConfig()
        self.movie_base_url = self.config.movie_base_url

    def _get_request(self, endpoint: str, params: Optional[dict] = None) -> httpx.Response:
        """Méthode interne pour gérer les appels HTTP avec Backoff conditionnel."""
        url = f"{self.movie_base_url}{endpoint}"
        
        # Définition de la fonction de requête
        def make_request():
            response = httpx.get(url, params=params)
            response.raise_for_status()
            return response

        # Si le backoff est activé dans la config, on enveloppe la fonction
        if self.config.movie_backoff:
            # On crée un wrapper dynamique
            wrapper = backoff.on_exception(
                backoff.expo,
                (httpx.HTTPError, httpx.TimeoutException),
                max_time=self.config.movie_backoff_max_time
            )(make_request)
            return wrapper()
        else:
            return make_request()

    def _format_output(self, data: Any, model: Any, output_format: Literal["pydantic", "dict", "pandas"]):
        if output_format == "pydantic":
            return [model(**item) for item in data]
        elif output_format == "dict":
            return data
        elif output_format == "pandas":
            return pd.DataFrame(data)
        else:
            raise ValueError("Invalid output_format. Choose from 'pydantic', 'dict', or 'pandas'.")

    def health_check(self) -> dict:
        response = self._get_request("/")
        return response.json()

    def get_movie(self, movie_id: int) -> MovieDetailed:
        response = self._get_request(f"/movies/{movie_id}")
        return MovieDetailed(**response.json())

    def list_movies(
        self,
        skip: int = 0,
        limit: int = 100,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        output_format: Literal["pydantic", "dict", "pandas"] = "pydantic"
    ) -> Union[List[MovieSimple], List[dict], "pd.DataFrame"]:
        params = {"skip": skip, "limit": limit}
        if title:
            params["title"] = title
        if genre:
            params["genre"] = genre
            
        response = self._get_request("/movies", params=params)
        return self._format_output(response.json(), MovieSimple, output_format)

    def get_rating(self, user_id: int, movie_id: int) -> RatingSimple:
        response = self._get_request(f"/ratings/{user_id}/{movie_id}")
        return RatingSimple(**response.json())

    def list_ratings(
        self,
        skip: int = 0,
        limit: int = 100,
        movie_id: Optional[int] = None,
        user_id: Optional[int] = None,
        min_rating: Optional[float] = None,
        output_format: Literal["pydantic", "dict", "pandas"] = "pydantic"
    ) -> Union[List[RatingSimple], List[dict], "pd.DataFrame"]:
        params = {"skip": skip, "limit": limit}
        if movie_id:
            params["movie_id"] = movie_id
        if user_id:
            params["user_id"] = user_id
        if min_rating:
            params["min_rating"] = min_rating
            
        response = self._get_request("/ratings", params=params)
        return self._format_output(response.json(), RatingSimple, output_format)

    def get_tag(self, user_id: int, movie_id: int, tag_text: str) -> TagSimple:
        response = self._get_request(f"/tags/{user_id}/{movie_id}/{tag_text}")
        return TagSimple(**response.json())

    def list_tags(
        self,
        skip: int = 0,
        limit: int = 100,
        movie_id: Optional[int] = None,
        user_id: Optional[int] = None,
        output_format: Literal["pydantic", "dict", "pandas"] = "pydantic"
    ) -> Union[List[TagSimple], List[dict], "pd.DataFrame"]:
        params = {"skip": skip, "limit": limit}
        if movie_id:
            params["movie_id"] = movie_id
        if user_id:
            params["user_id"] = user_id
            
        response = self._get_request("/tags", params=params)
        return self._format_output(response.json(), TagSimple, output_format)

    def get_link(self, movie_id: int) -> LinkSimple:
        response = self._get_request(f"/links/{movie_id}")
        return LinkSimple(**response.json())

    def list_links(
        self,
        skip: int = 0,
        limit: int = 100,
        output_format: Literal["pydantic", "dict", "pandas"] = "pydantic"
    ) -> Union[List[LinkSimple], List[dict], "pd.DataFrame"]:
        params = {"skip": skip, "limit": limit}
        response = self._get_request("/links", params=params)
        return self._format_output(response.json(), LinkSimple, output_format)

    def get_analytics(self) -> AnalyticsResponse:
        response = self._get_request("/analytics")
        return AnalyticsResponse(**response.json())