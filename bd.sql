PGDMP         8    	        	    p         
   rdf2subdue    9.1.6    9.1.6     |           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                       false            }           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                       false            ~           1262    27509 
   rdf2subdue    DATABASE     |   CREATE DATABASE rdf2subdue WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'es_ES.UTF-8' LC_CTYPE = 'es_ES.UTF-8';
    DROP DATABASE rdf2subdue;
             postgres    false                        2615    2200    public    SCHEMA        CREATE SCHEMA public;
    DROP SCHEMA public;
             postgres    false                       0    0    SCHEMA public    COMMENT     6   COMMENT ON SCHEMA public IS 'standard public schema';
                  postgres    false    5            �           0    0    public    ACL     �   REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;
                  postgres    false    5            �            3079    11683    plpgsql 	   EXTENSION     ?   CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;
    DROP EXTENSION plpgsql;
                  false            �           0    0    EXTENSION plpgsql    COMMENT     @   COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';
                       false    165            �            1259    27524    edges    TABLE     �   CREATE TABLE edges (
    origin integer NOT NULL,
    destination integer NOT NULL,
    label character varying NOT NULL,
    id integer NOT NULL
);
    DROP TABLE public.edges;
       public         postgres    false    5            �            1259    27542    edges_id_seq    SEQUENCE     n   CREATE SEQUENCE edges_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.edges_id_seq;
       public       postgres    false    162    5            �           0    0    edges_id_seq    SEQUENCE OWNED BY     /   ALTER SEQUENCE edges_id_seq OWNED BY edges.id;
            public       postgres    false    163            �           0    0    edges_id_seq    SEQUENCE SET     4   SELECT pg_catalog.setval('edges_id_seq', 1, false);
            public       postgres    false    163            �            1259    27510    nodes    TABLE     |   CREATE TABLE nodes (
    label character varying NOT NULL,
    id integer NOT NULL,
    "URI" character varying NOT NULL
);
    DROP TABLE public.nodes;
       public         postgres    false    5            �            1259    27553    nodes_id_seq    SEQUENCE     n   CREATE SEQUENCE nodes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.nodes_id_seq;
       public       postgres    false    161    5            �           0    0    nodes_id_seq    SEQUENCE OWNED BY     /   ALTER SEQUENCE nodes_id_seq OWNED BY nodes.id;
            public       postgres    false    164            �           0    0    nodes_id_seq    SEQUENCE SET     4   SELECT pg_catalog.setval('nodes_id_seq', 1, false);
            public       postgres    false    164            k           2604    27544    id    DEFAULT     V   ALTER TABLE ONLY edges ALTER COLUMN id SET DEFAULT nextval('edges_id_seq'::regclass);
 7   ALTER TABLE public.edges ALTER COLUMN id DROP DEFAULT;
       public       postgres    false    163    162            j           2604    27555    id    DEFAULT     V   ALTER TABLE ONLY nodes ALTER COLUMN id SET DEFAULT nextval('nodes_id_seq'::regclass);
 7   ALTER TABLE public.nodes ALTER COLUMN id DROP DEFAULT;
       public       postgres    false    164    161            y          0    27524    edges 
   TABLE DATA               8   COPY edges (origin, destination, label, id) FROM stdin;
    public       postgres    false    162    1914   G       x          0    27510    nodes 
   TABLE DATA               *   COPY nodes (label, id, "URI") FROM stdin;
    public       postgres    false    161    1914   d       s           2606    27552    edges_primary_key 
   CONSTRAINT     N   ALTER TABLE ONLY edges
    ADD CONSTRAINT edges_primary_key PRIMARY KEY (id);
 A   ALTER TABLE ONLY public.edges DROP CONSTRAINT edges_primary_key;
       public         postgres    false    162    162    1915            u           2606    27567    edges_unique_id 
   CONSTRAINT     G   ALTER TABLE ONLY edges
    ADD CONSTRAINT edges_unique_id UNIQUE (id);
 ?   ALTER TABLE ONLY public.edges DROP CONSTRAINT edges_unique_id;
       public         postgres    false    162    162    1915            m           2606    27565    nodes_id_primary 
   CONSTRAINT     M   ALTER TABLE ONLY nodes
    ADD CONSTRAINT nodes_id_primary PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.nodes DROP CONSTRAINT nodes_id_primary;
       public         postgres    false    161    161    1915            o           2606    27563    nodes_id_unique 
   CONSTRAINT     G   ALTER TABLE ONLY nodes
    ADD CONSTRAINT nodes_id_unique UNIQUE (id);
 ?   ALTER TABLE ONLY public.nodes DROP CONSTRAINT nodes_id_unique;
       public         postgres    false    161    161    1915            q           2606    27579    nodes_uri_unique 
   CONSTRAINT     K   ALTER TABLE ONLY nodes
    ADD CONSTRAINT nodes_uri_unique UNIQUE ("URI");
 @   ALTER TABLE ONLY public.nodes DROP CONSTRAINT nodes_uri_unique;
       public         postgres    false    161    161    1915            w           2606    27573    destination_foreign_key    FK CONSTRAINT     r   ALTER TABLE ONLY edges
    ADD CONSTRAINT destination_foreign_key FOREIGN KEY (destination) REFERENCES nodes(id);
 G   ALTER TABLE ONLY public.edges DROP CONSTRAINT destination_foreign_key;
       public       postgres    false    162    161    1902    1915            v           2606    27568    origin_foreign_key    FK CONSTRAINT     h   ALTER TABLE ONLY edges
    ADD CONSTRAINT origin_foreign_key FOREIGN KEY (origin) REFERENCES nodes(id);
 B   ALTER TABLE ONLY public.edges DROP CONSTRAINT origin_foreign_key;
       public       postgres    false    161    1902    162    1915            y      x������ � �      x      x������ � �     