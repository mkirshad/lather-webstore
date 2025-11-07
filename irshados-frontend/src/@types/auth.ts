export type OrganizationSummary = {
    organizationId: string
    organizationSlug: string
    organizationName: string
    role: string
}

export type SignInCredential = {
    email: string
    password: string
    organizationSlug: string
}

export type SignInResponse = {
    token: string
    user: {
        userId: string
        userName: string
        authority: string[]
        avatar?: string | null
        email: string
        activeOrganization: OrganizationSummary | null
        organizations: OrganizationSummary[]
    }
}

export type SignUpResponse = SignInResponse

export type SignUpCredential = {
    userName?: string
    email: string
    password: string
    organizationMode: 'existing' | 'new'
    organizationSlug?: string
    organizationName?: string
    organizationDomain?: string
    role?: string
}

export type ForgotPassword = {
    email: string
}

export type ResetPassword = {
    password: string
}

export type AuthRequestStatus = 'success' | 'failed' | ''

export type AuthResult = Promise<{
    status: AuthRequestStatus
    message: string
}>

export type User = {
    userId?: string | null
    avatar?: string | null
    userName?: string | null
    email?: string | null
    authority?: string[]
    activeOrganization?: OrganizationSummary | null
    organizations?: OrganizationSummary[]
}

export type Token = {
    accessToken: string
    refereshToken?: string
}

export type OauthSignInCallbackPayload = {
    onSignIn: (tokens: Token, user?: User) => void
    redirect: () => void
}
