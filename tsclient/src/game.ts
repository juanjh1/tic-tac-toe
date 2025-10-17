import { Database} from "./db.js"
import inquirer from "inquirer";
import { GameStatus } from "./enums/GameStatus.js";
import {Socket} from "node:net";
import { request } from "node:http";


export class Game{

	#isAutenticated: boolean; 
	#database: Database;
	static instance = new  Game(Database.instance) 
	
	private constructor(database: Database){
		this.#database = database;
		this.#isAutenticated = false;
	}
	
	async #autenticated(port: number , host: string , client: Socket):Promise<void>{
		
		this.#isAutenticated =  await this.#database.searchTokenUser(port, host);
		console.log(this.#isAutenticated)	
		if (!this.#isAutenticated){

			const {option} =  await inquirer.prompt([{
				type: "list",
				name: "option",
				message: "WELCOME TO TICTACTOE",
				choices: ["Login", "Register", "Exit"]}
			]);

			if(option == "Login"){
				const {username, password} = await this.#getUserCredetials();
				const request = {action:"login",username: username, password:password}
				client.write( JSON.stringify(request)+"\n");
				return	
			}

			if (option == "Exit"){
				return;
			}

			if (option == "Register"){
				const {username, password} = await this.#getUserCredetials();
				const request = {action:"register",username: username, password:password}
				client.write( JSON.stringify(request)+"\n");
				return;	
			}
		}
		
	}

	async start(port: number , host: string, client: Socket ): Promise<GameStatus>{
		
		await this.#autenticated(port, host, client);
		
		
		if(!this.#isAutenticated){

			return GameStatus.EXIT;
		}
		
		await this.#connection(client, port,host)
	
		return await this.#client_game(client)
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


	setSessionToken(token:string, port:number, host: string){
		
		this.#database.setSessionToken(token,port,host)
	}


	async #client_game(client: Socket): Promise<GameStatus>{
		
		
		const {clientOption} =  await inquirer.prompt([{
				type: "list",
				name: "clientOption",
				message: "TICTACTOE MAIN MENU",
				choices: ["Invite","List","Logout"]}
		]);

		switch(clientOption){
			case "Logout":
				const request = {action:"register"}
				client.write( JSON.stringify(request)+"\n");	
				break
			default:
			return GameStatus.EXIT;
		}
		return GameStatus.EXIT;
	}



	async #connection(client: Socket, port: number , host: string): Promise<void>{
		
		let token = this.#database.getTokenUser(port, host);

		if(!token){
			return;	
		}

		console.log("lo mandare")
		
		const request = {action:"connection"}

		client.write( JSON.stringify(request)+"\n")
		
	}
}
