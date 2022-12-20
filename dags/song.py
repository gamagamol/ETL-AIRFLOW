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
    query = 'select a."ArtistId", a."Name", a2."AlbumId", a2."Title", t."TrackId", t."Name",t."UnitPrice", t."Bytes", g."GenreId", g."Name" from "Artist" a left join "Album" a2 on a."ArtistId" = a2."ArtistId" left join "Track" t on t."AlbumId" = a2."AlbumId" join "Genre" g on g."GenreId" = t."GenreId" order by a."ArtistId",a2."AlbumId" asc '
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    songs = []
    for d in data:
        song = {
            'artist_id': d[0],
            'artist_name': d[1].replace("'", ""),
            'album_id': d[2],
            'album_title': d[3].replace("'", ""),
            'track_id': d[4],
            'track_name': d[5].replace("'", ""),
            'unit_price': float(d[6]),
            'bytes': d[7],
            'genre_id': d[8],
            'genre_name': d[9].replace("'", ""),
        }
        songs.append(song)
    songs=json.dumps(songs)
    return(songs)
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
    songs=json.loads(data)
    for d in songs:
        query = f"INSERT INTO public.songs(artist_id, artist_name, album_id, album_title, track_id, track_name, unit_price, bytes, genre_id, genre_name) VALUES ({d['artist_id']}, '{d['artist_name']}', {d['album_id']}, '{d['album_title']}', {d['track_id']}, '{d['track_name']}', {d['unit_price']}, {d['bytes']}, {d['genre_id']}, '{d['genre_name']}')"
        cursor.execute(query)
        connection.commit()
        
    cursor.close()
    print("success Inserting Data")
    


with DAG(
    dag_id='songs',
    default_args=default_args,
    description='Workflow for Datawarehouse Songs',
    start_date=datetime(2022, 12, 11),
    schedule_interval='0 7 */3 * *',

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
