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
	
	async #autenticated(port: number , host: string , client: Socket){
		
		this.#isAutenticated =  this.#database.searchUser(port, host);
		
		if (!this.#isAutenticated){

			while(true){
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
					break;
				}

				if (option == "Exit"){
					break;
				}

				if (option == "Register"){
					const {username, password} = await this.#getUserCredetials();
					const request = {action:"register",username: username, password:password}
					client.write( JSON.stringify(request)+"\n");
					break;	
				}
			}	
		
		}

	}

	start(port: number , host: string, client: Socket ): GameStatus{
		
		this.#autenticated(port, host, client);

		if(!this.#isAutenticated){

			return GameStatus.EXIT;
		}
		console.log("do somenting")

		return GameStatus.EXIT;
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
}
