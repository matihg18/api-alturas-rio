from client import PrefecturaClient
from parser import PrefecturaParser
from repository import ScraperRepository
from common.database import SessionLocal # Asumiendo que tenés esto en common

def main():
    client = PrefecturaClient()
    parser = PrefecturaParser()

    db = SessionLocal()
    repo = ScraperRepository(db)

    try:
        html = client.fetch_data()
        ports_data = parser.parse(html)

        repo.save_all(ports_data)
        print(f"Proceso finalizado. Se procesaron {len(ports_data)} puertos.")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()