
class LlumoAIError(Exception):
    """Base class for all Llumo SDK-related errors."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    @staticmethod
    def InvalidApiKey():
        return LlumoAIError("The provided API key is invalid or unauthorized"
                            "To fix this:\n"
        "1. Go to https://app.llumo.ai/getting-started\n"
        "2. Look at the top navigation bar (right side)\n"
        "3. Copy the API key shown under “API Key”\n"
        "4. Paste that key into your SDK configuration"
)

    @staticmethod
    def InvalidApiResponse():
        return LlumoAIError("Invalid or UnexpectedError response from the API"
                            "We received a response from the API, but it wasn’t in the expected format…”")

    @staticmethod
    def RequestFailed(detail="The request could not be completed."):
        return LlumoAIError(
            f"We were unable to complete the request to the Llumo API. "
            f"{detail} "
            "Please check your network connection or try again later."
        )


    @staticmethod
    def InvalidJsonResponse():
        return LlumoAIError("The API response is not in valid JSON format")

    @staticmethod
    def UnexpectedError(detail="Metric"):
        return LlumoAIError(
            f"We couldn’t find an evaluation named '{detail}'. "
            f"Please check that the name is correct. "
            f"If you’d like to run '{detail}', you can create a custom evaluation "
            f"with the same name at https://app.llumo.ai/evallm."
        )

    @staticmethod
    def EvalError(detail="Some error occured while processing"):
        return LlumoAIError(f"error: {detail}")

    @staticmethod
    def InsufficientCredits(details="Your available credits have been exhausted."):
        return LlumoAIError(
            f"{details} "
            "To continue running evaluations, please upgrade your plan or "
            "increase your usage limits in the LLUMO AI dashboard at: "
            "https://app.llumo.ai/settings."
        )

        # return LlumoAIError("LLumo hits exhausted")

    @staticmethod
    def InvalidPromptTemplate():
        return LlumoAIError('''Make sure the prompt template fulfills the following criteria:
        1. All the variables should be inside double curly braces. Example: Give answer for the {{query}}, based on given {{context}}.
        2. The variables used in the prompt template must be present in the dataframe columns with the same name..
        ''')

    @staticmethod
    def modelHitsExhausted(details = "Your credits for the selected model exhausted."):
        return LlumoAIError(details)

    @staticmethod
    def dependencyError(details):
        return LlumoAIError(details)

    @staticmethod
    def providerError(details):
        return LlumoAIError(details)

    @staticmethod
    def emptyLogList(details="No logs were provided for analysis."):
        return LlumoAIError(
            f"{details} "
            "Please pass at least one log entry. "
            "You can find the correct log format at "
            "https://app.llumo.ai/getting-started "
            "under the “Run SDK with zero data egress” section."
        )

    @staticmethod
    def invalidUserAim(details=""):
        return LlumoAIError(
            "Invalid userAim detected. "
            "Each userAim must match one of the supported categories used for analysis. "
            "Valid options include:\n"
            "[incorrectOutput, incorrectInput, hallucination, ragQuality, "
            "contextMismanagement, toolCallIssues, agentReasoning, stuckAgents, "
            "jsonErrors, highLatency, highCost, safetyBlocks, modelRouting, "
            "systemErrors, promptAdherence]."
        )


    # @staticmethod
    # def dateNotFound():
    #     return LlumoAIError("Trial end date or subscription end date not found for the given user.")
