declare namespace NodeJS {
    interface ProcessEnv {
      REACT_APP_SUPABASE_URL: string;
      REACT_APP_SUPABASE_ANON_KEY: string;
      // add other env variables as needed
    }
  }
  
  declare const process: {
    env: {
      [key: string]: string | undefined;
      REACT_APP_SUPABASE_URL?: string;
      REACT_APP_SUPABASE_ANON_KEY?: string;
    };
  };