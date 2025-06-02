import http.server
import socketserver
import urllib.parse
import html
import time
from query import load_lexicon, simple_search

lexicon, doc_id_map = load_lexicon('lexicon.pkl')
postings_path = 'postings.dat'
PORT = 8000

class SearchHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/':
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_page = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>IR Browser</title>
  <style>
    body {
      background-color: #f4f4f9;
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 0;
    }
    header {
      background-color: #4a76a8;
      color: white;
      padding: 1rem 0;
      text-align: center;
      font-size: 2rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    main {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-top: 3rem;
    }
    form {
      display: flex;
      gap: 0.5rem;
      width: 60%;
      max-width: 600px;
    }
    input[type="text"] {
      flex: 1;
      padding: 0.75rem;
      font-size: 1rem;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
    }
    button {
      padding: 0.75rem 1.5rem;
      font-size: 1rem;
      background-color: #4a76a8;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      transition: background-color 0.2s ease;
    }
    button:hover {
      background-color: #3b5f8a;
    }
    hr {
      width: 80%;
      margin-top: 2rem;
      border: none;
      border-top: 1px solid #ccc;
    }
  </style>
</head>
<body>
  <header>IR Browser</header>
  <main>
    <form action="/search" method="get">
      <input type="text" name="q" placeholder="Type your query here..." autofocus required />
      <button type="submit">Search</button>
    </form>
    <hr />
  </main>
</body>
</html>
"""
            self.wfile.write(html_page.encode('utf-8'))

        elif parsed.path == '/search':
            params = urllib.parse.parse_qs(parsed.query)
            query = params.get('q', [''])[0].strip()

            # Measure search time
            start = time.time()
            results = simple_search(query, lexicon, doc_id_map, postings_path, top_k=5)
            elapsed = (time.time() - start) * 1000  # in milliseconds
            print(f"[SEARCH] query='{query}' took {elapsed:.1f} ms")

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            header_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>IR Browser - Results</title>
  <style>
    body {
      background-color: #f4f4f9;
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 0;
    }
    header {
      background-color: #4a76a8;
      color: white;
      padding: 1rem 0;
      text-align: center;
      font-size: 2rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    main {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-top: 2rem;
      padding-bottom: 2rem;
    }
    form {
      display: flex;
      gap: 0.5rem;
      width: 60%;
      max-width: 600px;
      margin-bottom: 1.5rem;
    }
    input[type="text"] {
      flex: 1;
      padding: 0.75rem;
      font-size: 1rem;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
    }
    button {
      padding: 0.75rem 1.5rem;
      font-size: 1rem;
      background-color: #4a76a8;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      transition: background-color 0.2s ease;
    }
    button:hover {
      background-color: #3b5f8a;
    }
    .results {
      width: 80%;
      max-width: 800px;
      background-color: white;
      padding: 1.5rem;
      border-radius: 4px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .results h2 {
      margin-top: 0;
      font-size: 1.5rem;
      color: #333;
    }
    .results ol {
      padding-left: 1.2rem;
    }
    .results li {
      margin: 0.6rem 0;
      font-size: 1rem;
    }
    .results a {
      color: #4a76a8;
      text-decoration: none;
    }
    .results a:hover {
      text-decoration: underline;
    }
    .no-results {
      font-style: italic;
      color: #666;
    }
    .timing {
      margin-top: 1rem;
      font-size: 0.9rem;
      color: #555;
    }
  </style>
</head>
<body>
  <header>IR Browser</header>
  <main>
    <form action="/search" method="get">
      <input type="text" name="q" value="{escaped_query}" placeholder="Type your query here..." required />
      <button type="submit">Search</button>
    </form>
    <div class="results">
"""

            safe_query = html.escape(query)
            if not query:
                response_body = "<p class='no-results'>No query provided.</p></div></main></body></html>"
                full_response = header_html.replace("{escaped_query}", "") + response_body
                self.wfile.write(full_response.encode('utf-8'))
                return

            if not results:
                body = f"<h2>Results for: “{safe_query}”</h2><p class='no-results'>No documents found.</p>"
            else:
                body = f"<h2>Results for: “{safe_query}”</h2><ol>"
                for url in results:
                    safe_url = html.escape(url)
                    body += f'<li><a href="{safe_url}" target="_blank">{safe_url}</a></li>'
                body += "</ol>"

            # Show timing below results
            timing_html = f'<p class="timing">Search time: {elapsed:.1f} ms</p>'
            footer_html = "</div>" + timing_html + "</main></body></html>"

            full_response = header_html.replace("{escaped_query}", safe_query) + body + footer_html
            self.wfile.write(full_response.encode('utf-8'))

        else:
            self.send_error(404)

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), SearchHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()
