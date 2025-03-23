-- public.graficos definition

-- Drop table

-- DROP TABLE public.graficos;

CREATE TABLE public.graficos (
	id serial4 NOT NULL,
	nome varchar(255) NULL,
	eixo_x varchar(255) NULL,
	eixo_y varchar(255) NULL,
	filtros jsonb NULL,
	data_criacao timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	tipo_grafico varchar(255) NULL,
	"path" varchar(255) NULL,
	CONSTRAINT graficos_pkey PRIMARY KEY (id)
);