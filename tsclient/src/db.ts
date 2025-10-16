import sqlite3 from 'sqlite3';


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

	#createHost(port: number, host: string): void {
		
		this.#db.run("SELECT * FROM servers where ip=? and port=?",[host, port], 
			(result: sqlite3.RunResult, error: Error|null) => {
				
				if(!result){
					this.#db.run("INSERT INTO servers (ip, port) values (?,?)",[host, port])	
				}
				
				if(error){
					console.error(error);
				}
				return;
			}
		);
	}
	

	searchUser(port: number, host: string): boolean {
		
		let isAutenticated: boolean = false
		this.#createHost(port, host);
		
		this.#db.run("SELECT port FROM servers where ip=? and port=?",[host, port], 
			
			(result: sqlite3.RunResult, error: Error|null) => {
				if(result){
					isAutenticated = true;
				}
				console.log(`result: {result}`)	
				if (error){
					console.error(error)
				}
			}
		)

	        return isAutenticated;
	}

}

