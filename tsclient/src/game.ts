import { Database} from "./db.js"
import inquirer from "inquirer";
import { GameStatus } from "./enums/GameStatus.js";
import {Socket} from "node:net";


type Action = {
	action: string,
	session_token?: string,
	reason?: string
	users?: string[]
	
}

export class Game{

	#isAutenticated: boolean; 
	#database: Database;
	static instance = new  Game(Database.instance) 
	
	private constructor(database: Database){
		this.#database = database;
		this.#isAutenticated = false;
	}
	
	async #autenticated(port: number , host: string , client: Socket):Promise<GameStatus>{
		
		this.#isAutenticated =  await this.#database.searchTokenUser(port, host);
		
		console.log(this.#isAutenticated)	
		
		if (!this.#isAutenticated){

			const {option} =  await inquirer.prompt(
				[
					{
					type: "list",
					name: "option",
					message: "WELCOME TO TICTACTOE",
					choices: ["Login", "Register", "Exit"]
					}
				]
			);

			if(option == "Login"){
				
				const {username, password} = await this.#getUserCredetials();
				const request = {action:"login",username: username, password:password}
				client.write( JSON.stringify(request)+"\n");
			}

			if (option == "Exit"){
				
				return new Promise<GameStatus>((res, rej)=>{res(GameStatus.EXIT)});	
			}

			if (option == "Register"){
				
				const {username, password} = await this.#getUserCredetials();
				const request = {action:"register",username: username, password:password}
				
				client.write( JSON.stringify(request)+"\n");
			}

			return new Promise<GameStatus>((res, rej)=>{res(GameStatus.NOTHING)}); 
		}
		return new Promise<GameStatus>((res, rej)=>{res(GameStatus.AUTH)});	
	}

	async #start(port: number , host: string, client: Socket ): Promise<GameStatus>{
		
		let status : GameStatus = await this.#autenticated(port, host, client);
		
		
		if(!this.#isAutenticated &&  status == GameStatus.EXIT){

			return GameStatus.EXIT;
		}

		if(!this.#isAutenticated){
			
			return GameStatus.NOTHING;
		
		}
		
		await this.#connection(client, port,host)
	
		return await this.#client_game(client,port, host)
	}
	
	runClient( port: number, host: string, client: Socket,response?: Action , ): Promise<GameStatus>{
		//probably its better a switch sentence, a repository pattern is to much
			
		if(!response){
			
			return Game.instance.#start(port,host,client)
		
		}

		console.debug(response)

		if (response.action == "login_ok"){
			
			let token : string= response.session_token ?? ""
			
			if (token == ""){
				
				console.error("The login message don't have a token")
				
			}	
			
			return Game.instance.login(token, port, host,client )
		}

		if(response.action == "logout_ok"){
			
			return this.#logout(port, host,client )
		}

		if (response.action == "logout_bad"){
			// do somenting 
			return new Promise<GameStatus>((res, rej)=>{res(GameStatus.EXIT)});	
		}


		if (response.action ==  "re_login"){
			
			this.#reLogin(port, host,client);	
		
		}


		if (response.action == "list"){
			
			let users : string[] = response.users ?? [];
	
			for(let i = 0; i < users.length ; i++){
				
				console.log(`[+]: ${users[i]}`)
			}
			return this.#start(port,host,client)
		}
			
		return new Promise<GameStatus>((res, rej)=>{res(GameStatus.NOTHING)});	

		
		
	}


	async #getUserCredetials(): Promise<{username:string, password:string }>{
		
		const {username} =  await inquirer.prompt(
			[	
				{
				type: "input",
				name: "username",
				message: "username",
				}
			]
		);

		const {password} =  await inquirer.prompt(
			[
				{
				type: "input",
				name: "password",
				message: "password",
				}
			]
		);
		return {username, password};

	}

	async login(token:string, port:number, host: string, client: Socket): Promise<GameStatus>{
		
		await this.#setSessionToken(token, port, host)
		return await this.#start(port, host,client)	
	
	}


	#setSessionToken(token:string, port:number, host: string){
		
		this.#database.setSessionToken(token,port,host)
	}


	async #client_game(client: Socket, port: number, host: string ): Promise<GameStatus>{
		
		
		const {clientOption} =  await inquirer.prompt(
			[
				{
					type: "list",
					name: "clientOption",
					message: "TICTACTOE MAIN MENU",
					choices: ["Invite","List","Logout"]
				}
			]
		);
		
		const token: string = await this.#database.getTokenUser(port, host) ?? "" 
				
		if(token == ""){
	
			this.#isAutenticated = false
			return this.#start(port,host,client);
		
		}

		switch(clientOption){
			
			case "Logout":{
				
				let request = { action : "logout", session_token: token };
				
				client.write( JSON.stringify(request)+"\n");	
				
				break
			}
			case "List":{
				
				let request = { action : "list", session_token: token };
				
				client.write( JSON.stringify(request)+"\n");	
					
				break
			}
			default:

				return GameStatus.NOTHING;
		}
		return GameStatus.NOTHING;
	}
	
	async #reLogin (port: number, host: string, client:Socket ): Promise<GameStatus> {
		
		this.#database.deleteSessionToken(port, host);
		
		return this.#start(port,host,client)
		
	}


	async #connection(client: Socket, port: number , host: string): Promise<void>{
		
		let token = await this.#database.getTokenUser(port, host);

		if(!token){
			
			return;	
		}

		const request = {action:"connection", session_token: token}

		client.write( JSON.stringify(request)+"\n");
		
	}

	async #logout (port: number, host: string, client:Socket ): Promise<GameStatus> {
	
		this.#database.deleteSessionToken(port, host);
	
		return this.#start(port,host,client)
	
	}
}
