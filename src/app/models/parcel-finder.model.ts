export interface IFindParcelresponse {
  cadastralReference: string,
  geometry: IParcelGeometry,
  imagePath: string,
  metadata: IParcelMetadata,
  isDetailedDescription: boolean,
  hasBeenDescribed: boolean,
  parcelInfo: string,
}

export interface IParcelGeometry {
  CRS: string | null,
  coordinates: [number, number][];
  type:string
}

export interface IParcelMetadata {
  arboles: [number, number][];
  convergencia: {
    cat_fechaultimaconv: string
  }
  id: string[],
  isRecin: boolean,
  parcelaInfo: IParcelaInfo,
  query: IQuery[]
  usos: IUsosSigpac[]
  vigencia: string,
  vuelo: {
    fecha_vuelo: number
  }
}

export interface IParcelaInfo {
  agregado: number,
  dn_surface: number,
  municipio: string,
  parcela: number,
  poligono: number,
  provincia: string,
  referencia_cat: string
}

export interface IQuery {
  admisibilidad: number,
  altitud: number,
  coef_regadio: number,
  dn_surface: number,
  incidencias: string, 
  inctexto: string,
  pendiente_media: number,
  recinto: number,
  region: string,
  superficie_admisible: number,
  uso_sigpac: string
}

export interface IUsosSigpac {
  dn_superficie: number,
  superficie_admisible: number,
  uso_sigpac: string
}