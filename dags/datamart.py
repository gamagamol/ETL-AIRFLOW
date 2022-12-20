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
        database="datawarehouse"
    )
    cursor = connection.cursor()
    query = 'select distinct  a.invoice_date, a.artist_id,a.artist_name, total_revenue_hari, total_lagu_per_artist, lagu_kota, billing_city from(select invoice_date, artist_id,artist_name, sum(total) as total_revenue_hari from artist_revenue ar group by artist_id, invoice_date,artist_name order by artist_id  asc) a join(select artist_id, billing_city, count(t.track_id) as lagu_kota from "transaction" t  group by artist_id, billing_city order by artist_id  asc)b on a.artist_id = b.artist_id join(select artist_id, count(track_id) as total_lagu_per_artist from songs s  group by artist_id, genre_id order by artist_id  asc) c on a.artist_id = c.artist_id order by invoice_date, a.artist_id '
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    # return data
    datamart = []
    for d in data:
        data = {
            'date':str(d[0]),
            'artist_id':d[1],
            'artist_name': d[2].replace("'",""),
            'total_revenue_day':float(d[3]),
            'billing_city':str(d[6]),
            'total_song_artist':int(d[4]),
            'total_song_city':int(d[5]),
        }
        datamart.append(data)
    datamart = json.dumps(datamart)
    return (datamart)
    # return(songs)


def InsertData(ti):
    connection = psycopg2.connect(
        user="airflow",
        password="airflow",
        host="host.docker.internal",
        port="5434",
        database="datamart"
    )
    cursor = connection.cursor()

    data = ti.xcom_pull('ReadData')
    datamart = json.loads(data)
    for d in datamart:
        query = f"INSERT INTO public.data_mart(date, artist_id, artist_name, total_revenue_day, billing_city, total_song_artist, total_song_city) VALUES ('{d['date']}',{d['artist_id']},'{d['artist_name']}',{d['total_revenue_day']},'{d['billing_city']}',{d['total_song_artist']},{d['total_song_city']} )"
        # print(query)
        cursor.execute(query)
        connection.commit()

    cursor.close()
    print("success Inserting Data")


with DAG(
    dag_id='DataMart',
    default_args=default_args,
    description='Workflow for Datawarehouse DataMart',
    start_date=datetime(2022, 12, 12),
    schedule_interval='0 9 * * *',

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
