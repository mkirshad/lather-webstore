import { cloneElement } from 'react'
import HelpPanel from '@/components/template/HelpPanel'
import type { CommonProps } from '@/@types/common'

type SideProps = CommonProps

const Side = ({ children, ...rest }: SideProps) => {
    return (
        <div className="relative flex h-full p-6 bg-white dark:bg-gray-800">
            <div className="absolute right-6 top-6 z-10">
                <HelpPanel
                    hoverable={false}
                    className="text-xl text-gray-500 hover:text-primary-500 dark:text-gray-200"
                />
            </div>
            <div className="flex flex-1 flex-col items-center justify-center">
                <div className="w-full max-w-[380px] px-8 xl:max-w-[450px]">
                    {children
                        ? cloneElement(children as React.ReactElement, {
                              ...rest,
                          })
                        : null}
                </div>
            </div>
            <div className="relative hidden flex-1 items-end justify-between rounded-3xl py-6 px-10 lg:flex xl:max-w-[520px] 2xl:max-w-[720px]">
                <img
                    src="/img/others/auth-side-bg.png"
                    className="absolute left-0 top-0 h-full w-full rounded-3xl"
                />
            </div>
        </div>
    )
}

export default Side
