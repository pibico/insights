export const TOKEN_TYPES = {
	EOF: 'EOF',
	NUMBER: 'NUMBER',
	OPEN_PARENTHESIS: 'OPEN_PARENTHESIS',
	CLOSE_PARENTHESIS: 'CLOSE_PARENTHESIS',
	OPERATOR_ADD: 'OPERATOR_ADD',
	OPERATOR_SUB: 'OPERATOR_SUB',
	OPERATOR_MUL: 'OPERATOR_MUL',
	OPERATOR_DIV: 'OPERATOR_DIV',
	OPERATOR_GT: 'OPERATOR_GT',
	OPERATOR_LT: 'OPERATOR_LT',
	OPERATOR_EQ: 'OPERATOR_EQ',
	OPERATOR_NEQ: 'OPERATOR_NEQ',
	OPERATOR_GTE: 'OPERATOR_GTE',
	OPERATOR_LTE: 'OPERATOR_LTE',
	OPEN_SQUARE_BRACKET: 'OPEN_SQUARE_BRACKET',
	CLOSE_SQUARE_BRACKET: 'CLOSE_SQUARE_BRACKET',
	COLUMN: 'COLUMN',
	FUNCTION: 'FUNCTION',
	ARGUMENT_SEPARATOR: 'ARGUMENT_SEPARATOR',
	FUNCTION_ARGUMENTS: 'FUNCTION_ARGUMENTS',
	STRING: 'STRING',
}

const FUNCTION_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$'

function isParenthesis(char) {
	return /^[()]$/.test(char)
}

function isWhiteSpace(char) {
	return /^\s$/.test(char)
}

function isNumber(char) {
	return /^[0-9]$/.test(char)
}

function isOpenSquareBracket(char) {
	return char === '['
}

function isArgumentSeparator(char) {
	return char === ','
}

function isQuote(char) {
	return char === '"' || char === "'"
}

function isOperator(char) {
	return (
		char === '+' ||
		char === '-' ||
		char === '*' ||
		char === '/' ||
		char === '>' ||
		char === '<' ||
		char === '=' ||
		char === '!=' ||
		char === '>=' ||
		char === '<='
	)
}

function getOperatorTokenType(operator) {
	switch (operator) {
		case '+':
			return TOKEN_TYPES.OPERATOR_ADD
		case '-':
			return TOKEN_TYPES.OPERATOR_SUB
		case '*':
			return TOKEN_TYPES.OPERATOR_MUL
		case '/':
			return TOKEN_TYPES.OPERATOR_DIV
		case '>':
			return TOKEN_TYPES.OPERATOR_GT
		case '<':
			return TOKEN_TYPES.OPERATOR_LT
		case '=':
			return TOKEN_TYPES.OPERATOR_EQ
		case '!=':
			return TOKEN_TYPES.OPERATOR_NEQ
		case '>=':
			return TOKEN_TYPES.OPERATOR_GTE
		case '<=':
			return TOKEN_TYPES.OPERATOR_LTE
		default:
			throw new Error(`Unknown operator: ${operator}`)
	}
}

export default function tokenize(expression, offset = 0) {
	// remove tabs, form-feed, carriage returns, and newlines
	expression = expression.replace(/\t\f\r\n/g, '')

	let cursor = 0
	let tokens = []
	let char = expression[cursor]

	function advance() {
		char = expression[++cursor]
	}

	function processNumberToken() {
		let number = ''
		while (isNumber(char) || (char == '.' && isNumber(expression[cursor + 1]))) {
			number += char
			advance()
		}
		tokens.push({
			type: TOKEN_TYPES.NUMBER,
			value: number,
		})
	}

	function processColumnToken() {
		tokens.push({
			type: TOKEN_TYPES.OPEN_SQUARE_BRACKET,
		})
		advance()

		let columnStr = ''
		while (char != ']' && cursor < expression.length) {
			columnStr += char
			advance()
		}
		if (columnStr.length) {
			const start = offset + cursor - columnStr.length
			const [table, column] = columnStr.split('.')
			tokens.push({
				type: TOKEN_TYPES.COLUMN,
				start: start,
				end: offset + cursor,
				value: {
					table: column ? table : null,
					column: column ? column : table,
				},
			})
		}

		if (char === ']') {
			tokens.push({
				type: TOKEN_TYPES.CLOSE_SQUARE_BRACKET,
			})
			advance()
		}
	}

	function processFunctionToken() {
		let fn = ''
		while (FUNCTION_CHARS.includes(char) && cursor < expression.length) {
			fn += char
			advance()
		}
		if (fn) {
			tokens.push({
				type: TOKEN_TYPES.FUNCTION,
				start: offset + cursor - fn.length,
				end: offset + cursor,
				value: fn,
			})
			if (char === '(') {
				tokens.push({
					type: TOKEN_TYPES.OPEN_PARENTHESIS,
				})
				advance()
			}
			let argsStart = cursor
			let closeParenthesis = expression.indexOf(')', cursor)
			let argsEnd = closeParenthesis > -1 ? closeParenthesis : expression.length
			let argsStr = expression.substring(argsStart, argsEnd)
			let fnArgs = tokenize(argsStr, offset + argsStart).filter(
				(token) => token.type !== TOKEN_TYPES.EOF
			)
			tokens = tokens.concat(fnArgs)

			cursor = argsEnd - 1
			advance()
			if (char === ')') {
				tokens.push({
					type: TOKEN_TYPES.CLOSE_PARENTHESIS,
				})
				advance()
			}
		}
	}

	function processStringToken() {
		let quote = char
		advance()
		let string = ''
		while (char != quote && cursor < expression.length) {
			string += char
			advance()
		}
		if (char == quote) {
			tokens.push({
				type: TOKEN_TYPES.STRING,
				value: string,
			})
			advance()
		}
	}

	while (cursor < expression.length) {
		if (isWhiteSpace(char)) {
			advance()
			continue
		}

		if (isOperator(char)) {
			tokens.push({
				type: getOperatorTokenType(char),
				value: char,
			})
			advance()
			continue
		}

		if (isParenthesis(char)) {
			tokens.push({
				type: char == ')' ? TOKEN_TYPES.OPEN_PARENTHESIS : TOKEN_TYPES.CLOSE_PARENTHESIS,
			})
			advance()
			continue
		}

		if (isArgumentSeparator(char)) {
			tokens.push({
				type: TOKEN_TYPES.ARGUMENT_SEPARATOR,
				value: char,
			})
			advance()
			continue
		}

		if (isNumber(char)) {
			processNumberToken()
			continue
		}

		if (isOpenSquareBracket(char)) {
			processColumnToken()
			continue
		}

		if (isQuote(char)) {
			processStringToken()
			continue
		}

		if (FUNCTION_CHARS.includes(char)) {
			processFunctionToken()
			continue
		}

		console.warn(`Unexpected character: ${char} while parsing expression: ${expression}`)
		break
	}

	tokens.push({
		type: TOKEN_TYPES.EOF,
	})

	return tokens
}
