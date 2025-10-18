import { resolve } from 'node:path';
import sqlite3 from 'sqlite3';

interface ServerRow {
  id: number;
  ip: string;
  port: number;
  sesion: string | null;
}


interface SessionRow{
  sesion: string | null;
}



export class Database{

	static instance = new Database();
	
	#db:sqlite3.Database; 

	private constructor(){
		this.#db = new sqlite3.Database("tictactoe.db",this.#handleDatabaseError)
		this.#createServerTable()
	}
	
	#handleDatabaseError(error:Error|null){
		
		if(error){
			console.error("Error opening database")
			return;
		}
		
		console.log("Database open")		

	}

	#createServerTable(){
		
		this.#db.run(`

			CREATE TABLE IF NOT EXISTS servers(
			 id INTEGER PRIMARY KEY AUTOINCREMENT,
			 ip varchar(15)NOT NULL,
			 port SMALLINT NOT NULL,
			 sesion TEXT 
			);
		`);

	}

	async #createHost(port: number, host: string): Promise<void> {
		

		await new Promise<void>(
		   async (res, rej)=>	{
				this.#db.get<ServerRow>("SELECT * FROM servers where ip=? AND port=?",[host, port], 
					
					( error: Error|null, row) => {
						
						if(!row){
							
							this.#db.run(
								"INSERT INTO servers (ip, port) values (?,?)",
								[host, port], 
								(err)=>
								{
									 if(err){
										rej(err)
									}

									res()
								}
							)
						}else{
							res()
						}
						
						
						rej(error);
					}
				);
			}
		);
	}
	
	async getTokenUser(port: number, host: string):Promise<string | undefined> {
		
		this.#createHost(port, host);
		
		const token : SessionRow | undefined = await new Promise< SessionRow | undefined >((res, rej) => {

			this.#db.get<SessionRow>("SELECT sesion FROM servers where ip=? and port=?",[host, port], 
			
				( error: Error|null, row) => {
				
					res(row)	
					
					if (error){
						
						rej(error)
					
					}
				}
			)

		})
		
	        return Promise.resolve( token.sesion);
	}


	async searchTokenUser(port: number, host: string):Promise<boolean> {
		
		await this.#createHost(port, host);
		
		const ok : SessionRow | undefined = await new Promise< SessionRow | undefined >((res, rej) => {

			this.#db.get<SessionRow>("SELECT sesion FROM servers where ip=? and port=?",[host, port], 
			
				( error: Error|null, row) => {
				
					res(row)	
					
					if (error){
						
						rej(error)
					
					}
				}
			)

		})
			
	        return ok?.sesion != null? true: false;
	}
	

	async setSessionToken(token:string, port:number, host: string): Promise<void>{
		
		try{
			await new Promise ((res, rej) => {
				
				this.#db.run("UPDATE servers SET sesion=? where ip=? and port=? ",[token, host, port], 
						
					(error:Error|null)=>{
					
						if(error){
						
							rej(error.message)
						}
					}
				)

			})
		}catch(error){
		
			console.error(error)
		
		}
	}

	async deleteSessionToken(port:number, host: string): Promise<void>{
		
		try{
			await new Promise ((res, rej) => {
				
				this.#db.run("UPDATE servers SET sesion=NULL where ip=? and port=? ",[host, port], 
						
					(error:Error|null)=>{
					
						if(error){
						
							rej(error.message)
						}
					}
				)

			})
		}catch(error){
		
			console.error(error)
		
		}
	}

}

