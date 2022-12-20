from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
import json
import psycopg2



default_args = {
    'owner': 'Gama Ariefsadya',
    'retries': 5,
    'retry_delay': timedelta(minutes=2)

}

def ReadData():
    connection = psycopg2.connect(
        user="airflow",
        password="airflow",
        host="host.docker.internal",
        port="5434",
        database="chinook"
    )
    cursor = connection.cursor()
    query = 'select b.*, (select sum("Quantity" * "UnitPrice") from "InvoiceLine" il where b."TrackId"=il."TrackId" group  by "TrackId"=b."TrackId") as total from (select a."ArtistId", a."Name" as ArtistName, a2."AlbumId", a2."Title", t."TrackId", t."Name",il."InvoiceLineId", i."InvoiceId", i."InvoiceDate" from "Artist" a left join "Album" a2 ON a2."ArtistId"=a."ArtistId" left join "Track" t on t."AlbumId"=a2."AlbumId" join "InvoiceLine" il on il."TrackId"=t."TrackId" join "Invoice" i on i."InvoiceId"=il."InvoiceLineId" order by a."ArtistId" asc) b'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    revenues = []
    for d in data:
        revenue = {
            'artist_id': d[0],
            'artist_name': d[1].replace("'", ""),
            'album_id': d[2],
            'album_title': d[3].replace("'", ""),
            'track_id': d[4],
            'track_name': d[5].replace("'", ""),
            'invoice_line_id': d[6],
            'invoice_id': d[7],
            'invoice_date': str(d[8]),
            'total':float(d[9]),
        }
        revenues.append(revenue)
    revenues=json.dumps(revenues)
    return(revenues)
    # return(songs)


def InsertData(ti):
    connection = psycopg2.connect(
        user="airflow",
        password="airflow",
        host="host.docker.internal",
        port="5434",
        database="datawarehouse"
    )
    cursor = connection.cursor()

    data=ti.xcom_pull('ReadData')
    revenues=json.loads(data)
    for d in revenues:
        query = f"INSERT INTO public.artist_revenue(artist_id, artist_name, album_id, album_title, track_id, track_name, invoice_line_id, invoice_id, invoice_date, total) VALUES ({d['artist_id']}, '{d['artist_name']}', {d['album_id']}, '{d['album_title']}', {d['track_id']}, '{d['track_name']}', {d['invoice_line_id']}, {d['invoice_id']}, '{d['invoice_date']}', {d['total']})"
        cursor.execute(query)
        connection.commit()
        
    cursor.close()
    print("success Inserting Data")
    


with DAG(
    dag_id='ArtistRevenue',
    default_args=default_args,
    description='Workflow for Datawarehouse ArtistRevenue',
    start_date=datetime(2022, 12, 11),
    schedule_interval='0 7 * * *',

) as dag:
    task1 = PythonOperator(
        task_id='ReadData',
        python_callable=ReadData

    )
    task2 = PythonOperator(
        task_id='InsertData',
        python_callable=InsertData

    )
    
    
    
    task1 >> task2
