import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote

class AnnasArchiveScraper:
    BASE_URL = "https://annas-archive.li"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def search(self, query, lang=None, ext=None, sort=None, page=1):
        params = {"q": query}
        if lang:
            params["lang"] = lang
        if ext:
            params["ext"] = ext
        if sort:
            params["sort"] = sort
        if page > 1:
            params["page"] = str(page)
            
        url = f"{self.BASE_URL}/search?{urlencode(params)}"
        print(f"Fetching: {url}")
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return self._parse_search_results(response.text)

    def _parse_search_results(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        
        # Results are usually links with /md5/ prefix
        item_links = soup.select('a[href^="/md5/"]')
        
        seen_md5s = set()
        for link in item_links:
            href = link.get('href', '')
            md5 = href.split('/')[-1]
            if md5 in seen_md5s:
                continue
            
            # Find the main container for this result
            # Based on inspection, it's a flex container
            container = link.find_parent('div', class_='flex')
            if not container:
                # Try another parent if the direct flex is not found
                container = link.find_parent('div')
                if not container:
                    continue

            # Skip small links/icons
            if len(container.get_text(strip=True)) < 20:
                continue

            # Title - usually in an h3 or with font-semibold
            title_tag = container.select_one('h3')
            if not title_tag:
                title_tag = container.select_one('.font-semibold')
            
            title = title_tag.get_text(strip=True) if title_tag else ""
            if not title:
                continue

            seen_md5s.add(md5)

            # Author - usually a link with iconic prefix
            author = "Unknown"
            author_tag = container.find('a', href=lambda x: x and '/search?q=' in x and not any(k in x for k in ['ext=', 'lang=', 'sort=']))
            if author_tag:
                author = author_tag.get_text(strip=True)
            
            # Thumbnail
            img_tag = container.select_one('img')
            thumbnail = img_tag.get('src') if img_tag else None

            # Metadata line
            metadata_text = ""
            meta_div = container.find('div', class_=lambda x: x and ('text-gray-800' in x or 'text-slate-400' in x))
            if meta_div:
                metadata_text = meta_div.get_text(strip=True)
            
            parts = [p.strip() for p in metadata_text.split('·')]
            language = parts[0] if len(parts) > 0 else "Unknown"
            file_format = parts[1] if len(parts) > 1 else "Unknown"
            size = parts[2] if len(parts) > 2 else "Unknown"
            year = parts[3] if len(parts) > 3 else "Unknown"

            results.append({
                "title": title.replace('✅', '').strip(),
                "author": author,
                "md5": md5,
                "thumbnail": thumbnail,
                "language": language,
                "format": file_format,
                "size": size,
                "year": year,
                "url": f"{self.BASE_URL}{href}"
            })
            
        return results

    def get_detail(self, md5):
        url = f"{self.BASE_URL}/md5/{md5}"
        print(f"Fetching detail: {url}")
        
        response = self.session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Cover image
        img_tag = soup.select_one('img.object-cover')
        cover_image = img_tag.get('src') if img_tag else None
        
        # Download mirrors
        mirrors = []
        mirror_links = soup.select('a.js-download-link')
        for link in mirror_links:
            name = link.get_text(strip=True)
            href = link.get('href', '')
            
            if href.startswith('/'):
                href = f"{self.BASE_URL}{href}"
                
            if any(x in name.lower() for x in ["save", "edit", "report"]):
                continue
                
            mirrors.append({
                "name": name,
                "url": href
            })
            
        return {
            "md5": md5,
            "cover_image": cover_image,
            "mirrors": mirrors
        }

if __name__ == "__main__":
    scraper = AnnasArchiveScraper()
    test_query = "薬屋のひとりごと 10"
    results = scraper.search(test_query)
    if results:
        res = results[0]
        print(f"Title: {res['title']}")
        print(f"Author: {res['author']}")
        print(f"Thumbnail: {res['thumbnail']}")
        
        detail = scraper.get_detail(res['md5'])
        print(f"Cover Image: {detail['cover_image']}")
        print("Mirrors:")
        for m in detail['mirrors'][:3]:
            print(f"- {m['name']}: {m['url']}")
