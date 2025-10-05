export type Tokens = {
    access_token: string,
    refresh_token: string
    type: string
}

export enum UserRoleEnum {
    SUPER_ADMIN = "ROLE_SUPER_ADMIN",
    ADMIN = "ROLE_ADMIN",
    USER = "ROLE_USER",
}

type UserRole = {
    name: UserRoleEnum
    description: string | null
}

export type User = {
    username: string,
    email: string,
    disabled: boolean,
    created_at: string,
    role: UserRole
}
