import * as yup from "yup";
import type {InferType} from "yup";


export const loginFormSchema = yup
    .object({
        email: yup.string().email().required(),
        password: yup.string().required(),
    })

export type LoginValues = InferType<typeof loginFormSchema>;
