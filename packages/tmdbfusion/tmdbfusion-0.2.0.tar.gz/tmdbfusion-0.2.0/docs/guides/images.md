# Deep Dive: Image Handling Strategy

TMDB utilizes a predictable URL structure for images, but robust applications need to handle configuration changes and responsive sizing.

## URL Structure Anatomy

A TMDB image URL consists of three parts:

1. **Base URL**: `https://image.tmdb.org/t/p/`
2. **Size Token**: `w500`, `original`, etc.
3. **File Path**: `/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg` (returned by API)

Result: `https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg`

## Configuration Synchronization

The valid **Size Tokens** can theoretically change. `TMDBClient` allows you to sync these definitions from the API at runtime.

```python
# Updates internal lookup tables for 'w500', 'original', etc.
await client.sync_config() 
```

This updates `client.images.configuration`, which `get_image_url` reads from.

## Responsive Images (`srcset`)

For web applications, you should generate `srcset` attributes to serve the optimal image size.

```python
def generate_srcset(file_path: str) -> str:
    sizes = ["w300", "w780", "w1280", "original"]
    srcs = []
    
    for size in sizes:
        url = get_image_url(file_path, size)
        # Assuming 'original' is around 2000w, or extract width from string
        width_descriptor = size if size != "original" else "2000w" 
        srcs.append(f"{url} {width_descriptor}")
        
    return ", ".join(srcs)

# Output:
# .../w300/abc.jpg w300, .../w780/abc.jpg w780, ...
```

## Caching Strategy

TMDB Images are static. Once a file path is assigned, the image at that path rarely changes.

* **Browser Caching**: TMDB sends long `Cache-Control` headers.
* **CDN**: You should proxy these images through your own CDN (Cloudflare/Cloudfront) to respect TMDB's usage limits and improve latency.

> [!TIP]
> **Performance**: Do not hot-link directly to TMDB images in high-traffic production apps. Use the `get_image_url` output as the source for your own image optimization pipeline (e.g., Next.js Image Optimization).

## Placeholder Handling

The API returns `null` `poster_path` if no image exists. Your code must handle this.

```python
if movie.poster_path:
    url = get_image_url(movie.poster_path, "w500")
else:
    url = "/assets/fallback-poster.png"
```
