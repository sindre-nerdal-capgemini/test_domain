# Test urls
Modul for å kjøre tester mot et domene. Tester blan annet statuskode, response tid per ur. Og har også valget å følge alle redirects til de treffer 200 eller går i loop.

- **--domain** (Optional) Domene man vil kjøre mot. Defaults til ```https://ndla.no```
- **--requests-in-parallel** (Optional) Antall requests som skal kjøres parallelt. Default er at de kjører synkront, en etter en. Default er ```1```.
- **--test-requests-count-after-cached** (Optional) For å teste responsetid etter en cache er utløst må man spesifisere antall "cache triggers". Default er ```0```.
- **--should-follow-redirects** (Optional) Må settes til true hvis man er interressert i å følge etter response URl man får fra requests med status kode 300-399. Altså vil da følge redirects helt til den får en 200 eller har fått den samme URL i retur 5 ganger. Default er ```false```.
- **--meta-file** (Optional) Fil som spesifisere om siden inneholder DOM elementer og attributer. Defaults til ```dir_of_readme/meta.json```.
- **--timeout-between-each-chunk** (Optional) Timeout mellom hver request (i parllel). DVS hvis requests-in-parallel er 1, så vil det være timeout mellom hvert enkelt request. Hvis requests-in-parallel er 2, vil det være timeout etter hver 2. request. Default er ```0```.
- **--pdf-report** (Optional) Hvis man vil generere en pdf report.
- **--loggly-token** (Optional) Hvis man vil poste resultat til loggly.

### UrlFile
```
/
/relative/one
/realtive/two
```

### Metafile
- **description** er for å spesifisere en "label" for hva man prøver å hente fra dom.
- **method** hvilken metode som blir brukt (xpath, css_selector). Defaults til css_selector.
- **path** er stien til elementet i DOM.
- **should_be_present_in_dom** beskriver om elementet skal finnes eller ikke i DOM under test. Defaults til ```true```
```json
{
    "metas": [
        {
            "description": "Meta description tag",
            "path": "head > meta[name=\"description\"]"
        },
        {
            "description": "This element should not be present in dom",
            "path": "head > some > wrong > elm",
            "should_be_present_in_dom": false
        },
        {
            "description": "Using xpath",
            "method": "xpath",
            "path": "//*[contains(text(),'some string')]"
        },
    ]
}
```

#### Requirements
- Python 3.7
- Pip

#### Installation
```python F
# For å lage et virtuelltmiljø hvor man kan installere dependencies
python -m venv  path_to_folder

# Naviger så til root for å installere dependiencies
pip install -r requirements.txt
```

#### Running the script
```python
# For å kjøre scriptet
python run.py

# Vil teste alle en etter en.
# Tester også mot DOM elementer på hver URL.
python run.py --domain https://example.com --file "Path/To/urls.txt" --loggly-token "ad" --meta-file "Path/To/meta.json"

# Vil teste 3 urls om gangen i parallel
# Hvis man får en statuskode mellom 300-399, vil man følge location man får i response, for å se hvor alle redirectne ender.
python run.py -d https://example.com -f "Path/To/urls.txt" --should-follow-redirects true --requests-in-parallel 3
```

#### Loggly
For å poste til loggly må man legge til loggly token på ```LOGGLY_URL``` konstanten i scriptet ```run.py```.
I tillegg må man **IKKE** bruker argumentet ```--pdf-report```.

Objectet som blir postet til til loggly er da:
```json
{
    "timestamp": "",
    "logs":[
        {
            "log_line_number": 0,
            "request_url": "url",
            "timestamp": "",
            "request": {
                "header location": "",
                "response_time (ms)": 0,
                "size_in_bytes": 0,
                "status_code": 200,
                "meta": [
                    {
                        "css_selector": "",
                        "attributes": {
                            "attr_key": "",
                            "attr_key2": "",
                        },
                        "description": "",
                        "method": "",
                        "path": "",
                        "content": "",
                        "exists_in_dom": false,
                        "should_be_present_in_dom": false,
                    }
                ]
            }
        }
    ]
}

```